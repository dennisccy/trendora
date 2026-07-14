# Iteration diff (bounded)

Files changed: 10. Shown in full: 10.

```diff
diff --git a/README.md b/README.md
index 399abdc..bba9d56 100644
--- a/README.md
+++ b/README.md
@@ -31,6 +31,7 @@ Current capabilities:
   - **Downtrend Opportunity** — groups walk-forward observations by market state (causal phase, drawdown-severity band, or bear-probability band) and shows three ranked tables: "Held up best", "Fell hardest" (labelled research evidence only — no orders), and "Recovery-turn edge by phase". Each table is sortable, every `N=` chip opens exact underlying observations, and the study respects Episodes/Pooled and All-history/As-of toggles. A macro publication-lag disclosure is always shown.
   - All Research pages: every `N=` sample count is a clickable link that opens a drill-down in a new tab — keeping lab selections and scroll position undisturbed — showing exact stored observations; the observations table is sortable and filterable by ticker. From any observation row click the ticker to open that stock's detail page at the snapshot date in a new tab.
 - **Pre-registration registry**: a "Governance & process" section on the Research hub links, in one click, to a dedicated `/research/registry` page listing every trading hypothesis the platform has ever registered or tested — 11 rows today, each showing its exact selectors as compact, readable chips (e.g. `kind=factor`, `factor=vcp_contraction`, `decile=10`, `horizon=60`, `direction=positive`; a multi-leg combination's selectors render as one chip with legs joined by `+`), its economic rationale, registration date, source, and current status in a neutral gray badge — deliberately distinct from the green/red proven/not-proven coloring used on the Evidence page, so this column is never mistaken for a pass/fail signal. Every backfilled historical row carries a small "backfill" pill, and the page shows an honest loading skeleton, a contained error card if the backend is unreachable, or an empty state if the registry is ever empty. The registry is read-only — entries can only be added by the platform itself — and going forward the platform's evidence-certification process refuses to test any new idea that was not already logged here first, closing a common way statistical findings get quietly cherry-picked after the fact.
+- **Negative-results graveyard**: a second card next to Pre-registration registry in the Research hub's "Governance & process" section — "Negative-results graveyard" — opens a dedicated `/research/graveyard` page listing every hypothesis the platform has tested and rejected: 14 rows today, seven from the public evidence process plus, for the first time, seven from an internal early-stage research track whose results (rejections only — it has had no successes) were never shown anywhere before. Each row shows its exact cohort selectors as compact chips, whether it failed its out-of-sample test or simply didn't have enough data to judge, the date it was tested, the multiple-testing correction that was applied, which process produced it, and — where known — a lineage link back to its original registered hypothesis; clicking that link jumps straight to and highlights the exact matching row on the Pre-registration registry page. The one hypothesis retired for good (a moving-average pattern that failed twice) carries a "permanent" marker so nobody tries it again, and a "Revisit protocol" panel spells out in plain language the only way a rejected idea could ever be re-tested — every row links to it. Nothing about which values elsewhere read "Proven" changed; this page only makes the platform's past rejections auditable.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
 - **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
diff --git a/apps/backend/main.py b/apps/backend/main.py
index 404c521..bce536f 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -17,6 +17,7 @@ from fastapi.middleware.cors import CORSMiddleware
 
 from app.api import (
     backtest,
+    budget,
     dashboard,
     data,
     evidence,
@@ -136,6 +137,9 @@ def create_app() -> FastAPI:
     application.include_router(registry.router, prefix="/api")
     # goal-mcp-loop iter-31 (J-19) — the read-only negative-results graveyard (GET /api/research/graveyard).
     application.include_router(graveyard.router, prefix="/api")
+    # goal-mcp-loop iter-32 (J-17) — the read-only certification-budget accounting panel
+    # (GET /api/research/budget).
+    application.include_router(budget.router, prefix="/api")
     return application
 
 
diff --git a/apps/frontend/app/research/page.tsx b/apps/frontend/app/research/page.tsx
index 8128453..3917a37 100644
--- a/apps/frontend/app/research/page.tsx
+++ b/apps/frontend/app/research/page.tsx
@@ -14,6 +14,7 @@ import {
   Thermometer,
   TrendingDown,
   TrendingUp,
+  Wallet,
   Waves,
 } from "lucide-react";
 
@@ -76,10 +77,10 @@ export default function ResearchHubPage() {
         })}
       </div>
 
-      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) — Governance & process: registry + graveyard now,
-          budget / referee-audit still to follow. Kept a SEPARATE section, not an 11th RESEARCH_LABS
-          entry — that array's reading order is a J-113 contract over the ten analytical labs; a
-          governance/process link is architecturally distinct, not a lab. */}
+      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) / iter-32 (J-17) — Governance & process:
+          registry + graveyard + budget now; referee-audit still to follow. Kept a SEPARATE section,
+          not an 11th RESEARCH_LABS entry — that array's reading order is a J-113 contract over the ten
+          analytical labs; a governance/process link is architecturally distinct, not a lab. */}
       <div className="space-y-3">
         <h2 className="text-sm font-semibold uppercase tracking-wide text-text-faint">Governance &amp; process</h2>
         <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-governance">
@@ -124,6 +125,29 @@ export default function ResearchHubPage() {
               verdict, deflation context, and registration lineage. Nobody retries a dead idea blindly.
             </p>
           </Link>
+
+          {/* goal-mcp-loop iter-32 (J-17) — the certification-budget accounting panel: total trials,
+              the current canonical bar, Thresholdout budget remaining, and the staging LORD++ wealth —
+              so nothing silently spends the year's statistical credibility. */}
+          <Link
+            href={asofHref("/research/budget")}
+            data-testid="research-governance-link-budget"
+            className={cn(
+              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
+              "hover:border-accent hover:bg-surface-2",
+              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
+            )}
+          >
+            <div className="flex items-center gap-2">
+              <Wallet className="h-5 w-5 text-accent" aria-hidden />
+              <h3 className="text-base font-semibold text-text">Certification-budget accounting</h3>
+              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
+            </div>
+            <p className="text-sm text-text-muted">
+              Total trials, the current canonical bar, the Thresholdout budget remaining, and the
+              staging LORD++ wealth — each over time, re-read from the same referee/ledger accounting.
+            </p>
+          </Link>
         </div>
       </div>
     </div>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index acee670..d3b2ada 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -6,6 +6,7 @@
  */
 
 import { resolveApiBase } from "@/lib/api-base";
+import type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget } from "@/lib/budget";
 import type {
   CertifiedClaim,
   EvidenceLedgerResponse,
@@ -25,6 +26,9 @@ export type { PreRegistrationRow, RegistryResponse };
 // Re-export the negative-results graveyard types (goal-mcp-loop iter-31, J-19) alongside `fetchGraveyard`.
 export type { GraveyardEntry, GraveyardResponse, RevisitProtocol };
 
+// Re-export the certification-budget accounting types (goal-mcp-loop iter-32, J-17) alongside `fetchBudget`.
+export type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget };
+
 /** The build-time configured backend base (`NEXT_PUBLIC_API_URL`, default localhost). The configured
  *  backend PORT (`NEXT_PUBLIC_API_PORT`) is read alongside so the runtime resolver can host-swap to the
  *  page's own host when the page is opened at a non-localhost (LAN-IP) origin (J-108). Both are inlined
@@ -376,6 +380,17 @@ export async function fetchGraveyard(signal?: AbortSignal): Promise<GraveyardRes
   return getJSON<GraveyardResponse>("/api/research/graveyard", signal);
 }
 
+// --- certification-budget accounting (goal-mcp-loop iter-32, J-17 / backlog B-903) ----------
+/** GET /api/research/budget — the read-only certification-budget accounting panel: total canonical
+ *  trials to date, the current canonical `required_p` bar, the Thresholdout budget remaining, and the
+ *  staging LORD++ next-trial level — each with a per-trial spend-over-time series, re-read (or
+ *  re-derived via the SAME referee/ledger seams the certifier uses — never a parallel computation).
+ *  Introduces no proven-language. Throws on network error or non-200 so the page renders an explicit
+ *  "Backend unavailable" state. */
+export async function fetchBudget(signal?: AbortSignal): Promise<BudgetResponse> {
+  return getJSON<BudgetResponse>("/api/research/budget", signal);
+}
+
 // --- stock price/MA/volume series for the detail chart (iter-4) -----------------------------
 /** One ascending OHLCV bar. By default date <= as-of (no lookahead — the backend reads only
  *  `bars_asof`). With the J-20 `through=latest` opt-in the series extends through the latest seed bar
diff --git a/apps/backend/app/api/budget.py b/apps/backend/app/api/budget.py
new file mode 100644
index 0000000..a8cdcf4
--- /dev/null
+++ b/apps/backend/app/api/budget.py
@@ -0,0 +1,33 @@
+"""GET /api/research/budget — the read-only certification-budget accounting panel (goal-mcp-loop
+iter-32, J-17 / backlog B-903).
+
+Serves `app.engine.budget_accounting.build_budget_payload` verbatim (re-format only — no recompute):
+total canonical trials to date, the current canonical `required_p` bar, the Thresholdout budget
+remaining, and the staging LORD++ next-trial level — each with a per-trial spend-over-time series, all
+re-read from the SAME `ledger` / `online_fdr` / `referee` seams `app.mcp.tools.verify_edge` uses.
+
+No DB/session is needed (both ledgers are append-only state files, not the snapshot DB). Ledger paths
+are config/env-driven via the existing resolvers (anti-goal: No magic numbers — no path literal here).
+A missing/empty ledger (either or both) returns 200 with the honest empty-ledger accounting the
+formulas naturally produce, never a 500 (anti-goal: resilience to data-shape change).
+
+READ-ONLY, always: no proven-language — trial counts and alpha figures are descriptive accounting,
+never a "Proven"/"Not yet proven" signal. That continues to flow solely from `app.engine.evidence` /
+`GET /api/evidence`, untouched here.
+"""
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.engine.budget_accounting import build_budget_payload
+
+router = APIRouter(tags=["budget"])
+
+
+@router.get("/research/budget")
+def get_budget() -> dict:
+    """The certification-budget accounting payload, verbatim: `{"canonical": {...}, "staging": {...}}`.
+    READ-ONLY — recomputes nothing beyond the two forward next-trial bars (via the SAME seams
+    `verify_edge` uses). A missing/empty ledger (either or both) ⇒ the honest empty-ledger accounting
+    (200, never 500)."""
+    return build_budget_payload()
diff --git a/apps/backend/app/engine/budget_accounting.py b/apps/backend/app/engine/budget_accounting.py
new file mode 100644
index 0000000..50351a3
--- /dev/null
+++ b/apps/backend/app/engine/budget_accounting.py
@@ -0,0 +1,153 @@
+"""The certification-budget accounting panel — the read-side composition of the referee's own
+multiple-testing accounting (goal-mcp-loop iter-32, J-17 / backlog B-903).
+
+This module answers "how much statistical-credibility budget has already been spent, before any new
+scan is proposed" by RE-READING the exact seams `app.mcp.tools:verify_edge` already uses. It computes
+NO canonical value independently (B-903's named failure mode is "UI-recompute" — a parallel bookkeeping
+path that could silently disagree with the referee's own accounting):
+
+  - **Canonical** (`app.engine.ledger` + `app.engine.referee`, strict Bonferroni, ALWAYS): trials to
+    date = `ledger.count_trials(canonical_path)` (display value, kept SEPARATE from the forward-looking
+    ordinal below — never conflated); the forward next-trial ordinal `n_trials_next` = that count + 1;
+    the current bar `required_p = referee.DEFAULT_ALPHA_PER_TEST / n_trials_next` — the EXACT value the
+    next `verify_edge` call would compute (the constant is IMPORTED, never a `0.05` literal here).
+    Thresholdout budget remaining = `referee.DEFAULT_ALPHA_BUDGET - ledger.alpha_spent(canonical_path)`
+    (byte-identical to the `remaining` `verify_edge` computes at `tools.py:511`).
+  - **Staging** (`app.engine.online_fdr`, LORD++): the same `n_trials_next` shape, and the next-trial
+    significance level (the "alpha-wealth" B-903 asks to surface) via `online_fdr.test_level(n_trials_
+    next, ledger.rejection_offsets(staging_path), alpha=cfg.evidence.fdr.alpha, w0_fraction=cfg.evidence.
+    fdr.w0_fraction, gamma_exponent=cfg.evidence.fdr.gamma_exponent, gamma_terms=cfg.evidence.fdr.
+    gamma_terms)` — the IDENTICAL call `verify_edge` makes for a staging claim (config-sourced tunables
+    only, no literal).
+  - **Spend-over-time** (per ledger): every ORIGINAL entry (forward-walk monitoring records excluded,
+    the SAME exclusion `app.engine.graveyard` / `app.engine.evidence` already use), in append order,
+    re-displaying its OWN recorded `verdict.required_p` verbatim (both ledgers — the Bonferroni bar or
+    the LORD++ level THAT trial was actually judged at) plus `verdict.deflation_divisor` /
+    `verdict.alpha_charged` (canonical only — under LORD++ `deflation_divisor` just mirrors the trial
+    ordinal, not a meaningful divisor, so the staging series omits it). History is READ, never
+    recomputed; only the two forward next-trial figures above call a live function.
+
+Ledger paths come ONLY from the existing resolvers — `app.engine.evidence.resolve_ledger_path()`
+(canonical) and `app.engine.graveyard.resolve_staging_ledger_path()` (staging, REUSED rather than
+duplicated, per that module's own docstring). A missing/empty ledger degrades to an honest zero/empty
+snapshot (0 trials, `required_p = 0.05/1`, the full starting alpha budget, the staging economy's
+initial wealth) — never a raise; the formulas above naturally produce this on an empty ledger (`count_
+trials` / `alpha_spent` / `rejection_offsets` all return the empty-file default), so no special-casing
+is needed.
+
+READ-ONLY, always: this module writes nothing, and never touches `app.engine.referee.certify_edge`,
+`app.mcp.tools.verify_edge`, or either ledger's write path. It carries no proven-language — trial
+counts and alpha figures are descriptive accounting, never a "Proven"/"Not yet proven" signal (that
+stays the exclusive province of `app.engine.evidence` / `GET /api/evidence`, untouched here).
+"""
+from __future__ import annotations
+
+from typing import Any
+
+from app.config import get_config
+from app.engine import evidence as evidence_mod
+from app.engine import online_fdr
+from app.engine.graveyard import resolve_staging_ledger_path
+from app.engine.ledger import (
+    FORWARD_WALK_TYPE,
+    alpha_spent,
+    count_trials,
+    read_entries,
+    rejection_offsets,
+)
+from app.engine.referee import DEFAULT_ALPHA_BUDGET, DEFAULT_ALPHA_PER_TEST
+
+
+def _spend_over_time(ledger_path: str, *, staging: bool) -> list[dict]:
+    """Every ORIGINAL (non-forward-walk) entry in `ledger_path`, in append order, projected into one
+    spend-over-time point. `required_p` is re-read VERBATIM from the entry's OWN recorded verdict on
+    BOTH ledgers (canonical: the Bonferroni bar that trial was judged at; staging: the LORD++ level
+    that trial was judged at). `deflation_divisor` / `alpha_charged` ride along for the canonical series
+    only. Nothing is recomputed — every value is exactly what the referee wrote at the time of that
+    trial; `trial`/`register_date`/`status` are the minimal context a "spend-over-time" series needs to
+    plot (an ordinal + its date + its outcome), not a derived statistic."""
+    rows: list[dict] = []
+    ordinal = 0
+    for entry in read_entries(ledger_path):
+        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+            continue
+        ordinal += 1
+        verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
+        point: dict[str, Any] = {
+            "trial": ordinal,
+            "register_date": entry.get("register_date"),
+            "status": verdict.get("status"),
+            "required_p": verdict.get("required_p"),
+        }
+        if not staging:
+            point["deflation_divisor"] = verdict.get("deflation_divisor")
+            point["alpha_charged"] = verdict.get("alpha_charged")
+        rows.append(point)
+    return rows
+
+
+def _canonical_section(canonical_path: str) -> dict:
+    """The canonical (strict-Bonferroni) accounting: trials to date, the forward next-trial bar, the
+    Thresholdout budget remaining, and its spend-over-time series. `required_p` / `alpha_budget_
+    remaining` use ONLY the imported referee constants + the `ledger` seams — the exact formulas
+    `verify_edge` runs for the next real canonical claim."""
+    n_trials_to_date = count_trials(canonical_path)
+    n_trials_next = n_trials_to_date + 1
+    spent = alpha_spent(canonical_path)
+    return {
+        "n_trials_to_date": n_trials_to_date,
+        "n_trials_next": n_trials_next,
+        "alpha_per_test": DEFAULT_ALPHA_PER_TEST,
+        "required_p": DEFAULT_ALPHA_PER_TEST / n_trials_next,
+        "alpha_budget_total": DEFAULT_ALPHA_BUDGET,
+        "alpha_spent": spent,
+        "alpha_budget_remaining": DEFAULT_ALPHA_BUDGET - spent,
+        "spend_over_time": _spend_over_time(canonical_path, staging=False),
+    }
+
+
+def _staging_section(staging_path: str, fdr_cfg: Any) -> dict:
+    """The staging (LORD++) accounting: trials to date, the forward next-trial significance level (the
+    "alpha-wealth" figure B-903 asks to surface), and its spend-over-time series. `next_level` calls the
+    SAME `online_fdr.test_level` seam `verify_edge` uses for a staging claim, with config-sourced
+    tunables only (`cfg.evidence.fdr`) — this module names no LORD++ parameter as a literal."""
+    n_trials_to_date = count_trials(staging_path)
+    n_trials_next = n_trials_to_date + 1
+    next_level = online_fdr.test_level(
+        n_trials_next,
+        rejection_offsets(staging_path),
+        alpha=fdr_cfg.alpha,
+        w0_fraction=fdr_cfg.w0_fraction,
+        gamma_exponent=fdr_cfg.gamma_exponent,
+        gamma_terms=fdr_cfg.gamma_terms,
+    )
+    return {
+        "n_trials_to_date": n_trials_to_date,
+        "n_trials_next": n_trials_next,
+        "next_level": next_level,
+        "spend_over_time": _spend_over_time(staging_path, staging=True),
+    }
+
+
+def build_budget_payload(canonical_path: str | None = None, staging_path: str | None = None) -> dict:
+    """Compose the read-only `/api/research/budget` payload: `{"canonical": {...}, "staging": {...}}`.
+    `canonical_path` defaults to `app.engine.evidence.resolve_ledger_path()`; `staging_path` defaults to
+    `app.engine.graveyard.resolve_staging_ledger_path()` — the endpoint's real, no-argument call shape.
+    A test may pass explicit fixture paths instead (mirrors `app.engine.graveyard.build_graveyard_
+    payload`'s optional-path pattern).
+
+    RECOMPUTES NOTHING: every figure is either read verbatim from a recorded verdict, or produced by
+    calling the SAME `ledger` / `online_fdr` / `referee` seams `app.mcp.tools.verify_edge` calls for the
+    next real claim. A missing/empty ledger (either or both) degrades to the honest empty-ledger values
+    the formulas naturally produce (0 trials, `required_p = alpha_per_test / 1`, the full starting
+    budget, the staging economy's initial wealth) — never a crash (anti-goal: resilience to data-shape
+    change)."""
+    resolved_canonical = (
+        canonical_path if canonical_path is not None else evidence_mod.resolve_ledger_path()
+    )
+    resolved_staging = staging_path if staging_path is not None else resolve_staging_ledger_path()
+    fdr_cfg = get_config().evidence.fdr
+    return {
+        "canonical": _canonical_section(resolved_canonical),
+        "staging": _staging_section(resolved_staging, fdr_cfg),
+    }
diff --git a/apps/backend/tests/test_api_budget.py b/apps/backend/tests/test_api_budget.py
new file mode 100644
index 0000000..e40c482
--- /dev/null
+++ b/apps/backend/tests/test_api_budget.py
@@ -0,0 +1,95 @@
+"""GET /api/research/budget API tests (goal-mcp-loop iter-32, J-17 / backlog B-903).
+
+Mounts ONLY the budget router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and NO
+walk-forward boot -- the endpoint reads the two append-only ledger state files, not a snapshot (mirrors
+`test_api_graveyard.py`'s DB-free four-test shape exactly: 200-on-missing, verbatim serving,
+endpoint-equals-module, real-ledger status-derived count).
+"""
+from __future__ import annotations
+
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+
+from app.api import budget
+from app.engine.budget_accounting import build_budget_payload
+from app.engine.evidence import LEDGER_PATH_ENV, resolve_ledger_path
+from app.engine.graveyard import STAGING_LEDGER_PATH_ENV, resolve_staging_ledger_path
+from app.engine.ledger import append_entry, count_trials
+
+
+def _client() -> TestClient:
+    app = FastAPI()
+    app.include_router(budget.router, prefix="/api")
+    return TestClient(app)
+
+
+def test_budget_endpoint_200_honest_empty_on_missing_ledger_files(tmp_path, monkeypatch):
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing-canonical.jsonl"))
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
+    with _client() as client:
+        resp = client.get("/api/research/budget")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["canonical"]["n_trials_to_date"] == 0
+    assert body["canonical"]["required_p"] == 0.05
+    assert body["canonical"]["spend_over_time"] == []
+    assert body["staging"]["n_trials_to_date"] == 0
+    assert body["staging"]["spend_over_time"] == []
+
+
+def test_budget_endpoint_serves_a_fixture_entry_verbatim(tmp_path, monkeypatch):
+    canonical = tmp_path / "canonical.jsonl"
+    entry = {
+        "claim": {
+            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+            "horizon": 60, "direction": "positive",
+        },
+        "cohort_n": 100, "control_n": 50, "horizon": 60, "register_date": "2026-07-14",
+        "verdict": {
+            "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 1,
+            "required_p": 0.05, "alpha_charged": 0.0,
+        },
+    }
+    append_entry(str(canonical), entry)
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(canonical))
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
+    with _client() as client:
+        resp = client.get("/api/research/budget")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["canonical"]["n_trials_to_date"] == 1
+    assert body["canonical"]["n_trials_next"] == 2
+    assert body["canonical"]["required_p"] == 0.05 / 2
+    point = body["canonical"]["spend_over_time"][0]
+    assert point["required_p"] == 0.05
+    assert point["deflation_divisor"] == 1
+    assert point["alpha_charged"] == 0.0
+    assert point["register_date"] == "2026-07-14"
+    assert point["status"] == "FAIL"
+
+
+def test_budget_endpoint_equals_build_budget_payload_directly(monkeypatch):
+    """Single-source assertion: the endpoint's response equals `build_budget_payload()` called directly
+    against the SAME (real, committed) ledger files -- the page can never disagree with the composition
+    module."""
+    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
+    with _client() as client:
+        resp = client.get("/api/research/budget")
+    assert resp.status_code == 200
+    assert resp.json() == build_budget_payload()
+
+
+def test_budget_endpoint_real_ledgers_today_status_derived_trial_counts(monkeypatch):
+    """Status-derived, not a hardcoded literal (iter-30/31 lesson): the expected counts are COMPUTED
+    from the two real committed ledger files, not asserted as a bare "7"."""
+    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
+    expected_canonical = count_trials(resolve_ledger_path())
+    expected_staging = count_trials(resolve_staging_ledger_path())
+
+    with _client() as client:
+        resp = client.get("/api/research/budget")
+    body = resp.json()
+    assert body["canonical"]["n_trials_to_date"] == expected_canonical
+    assert body["staging"]["n_trials_to_date"] == expected_staging
diff --git a/apps/backend/tests/test_budget_accounting.py b/apps/backend/tests/test_budget_accounting.py
new file mode 100644
index 0000000..b733bfd
--- /dev/null
+++ b/apps/backend/tests/test_budget_accounting.py
@@ -0,0 +1,255 @@
+"""Certification-budget accounting composition tests (goal-mcp-loop iter-32, J-17 / backlog B-903).
+
+`app.engine.budget_accounting` is a PURE read-compose module: it re-reads the SAME `ledger` /
+`online_fdr` / `referee` seams `app.mcp.tools.verify_edge` uses -- it computes NO canonical value
+independently (B-903's named failure mode is "UI-recompute"). These tests pin:
+
+  - Single-source: the payload's canonical trials / `required_p` / budget-remaining, and the staging
+    next-trial level, equal values independently derived by calling those SAME seams directly against
+    the live ledgers (proves no parallel bookkeeping).
+  - Fixture-spend: appending fixture claims to a THROWAWAY `tmp_path` ledger moves the figures exactly
+    as hand-computed (trials n -> n+1; `required_p = 0.05/(n+1)`; a stable fixture charges
+    `alpha_charged=0` vs an overfit one charging the per-claim cost; the staging level recomputes per
+    LORD++). The REAL `certified-claims.jsonl` / `staging-ledger.jsonl` are never written by these tests.
+  - Resilience: missing/empty ledger -> the honest empty-ledger snapshot (0 trials, `required_p =
+    0.05/1`, the full starting budget, the staging economy's initial wealth); an all-FAIL ledger
+    depletes the staging next-trial level with no replenishment; spend-over-time series length ==
+    `count_trials` for that ledger; forward-walk monitoring records are excluded from both.
+"""
+from __future__ import annotations
+
+from app.config import REPO_ROOT, get_config
+from app.engine import online_fdr
+from app.engine.budget_accounting import build_budget_payload
+from app.engine.evidence import resolve_ledger_path
+from app.engine.graveyard import resolve_staging_ledger_path
+from app.engine.ledger import alpha_spent, append_entry, count_trials, rejection_offsets
+from app.engine.referee import DEFAULT_ALPHA_BUDGET, DEFAULT_ALPHA_PER_TEST
+
+_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
+_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
+
+
+def _entry(factor: str, *, horizon: int = 20, **verdict_extra) -> dict:
+    verdict = {
+        "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 1,
+        "required_p": 0.05, "alpha_charged": 0.0, "holdout_edge": -0.01, "p_value": 0.9,
+    }
+    verdict.update(verdict_extra)
+    return {
+        "claim": {
+            "kind": "factor", "factor": factor, "slice_kind": "decile", "decile": 10,
+            "horizon": horizon, "direction": "positive",
+        },
+        "cohort_n": 100, "control_n": 50, "horizon": horizon, "register_date": "2026-07-14",
+        "verdict": verdict,
+    }
+
+
+# ==================================================================================================
+# Single-source: payload figures equal values independently derived via the SAME seams verify_edge uses
+# ==================================================================================================
+def test_canonical_single_source_against_live_ledger():
+    payload = build_budget_payload()
+    canonical = payload["canonical"]
+    resolved = resolve_ledger_path()
+    expected_trials = count_trials(resolved)
+    expected_spent = alpha_spent(resolved)
+    assert canonical["n_trials_to_date"] == expected_trials
+    assert canonical["n_trials_next"] == expected_trials + 1
+    assert canonical["required_p"] == DEFAULT_ALPHA_PER_TEST / (expected_trials + 1)
+    assert canonical["alpha_spent"] == expected_spent
+    assert canonical["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET - expected_spent
+
+
+def test_staging_single_source_against_live_ledger():
+    payload = build_budget_payload()
+    staging = payload["staging"]
+    resolved = resolve_staging_ledger_path()
+    expected_trials = count_trials(resolved)
+    fdr_cfg = get_config().evidence.fdr
+    expected_level = online_fdr.test_level(
+        expected_trials + 1,
+        rejection_offsets(resolved),
+        alpha=fdr_cfg.alpha,
+        w0_fraction=fdr_cfg.w0_fraction,
+        gamma_exponent=fdr_cfg.gamma_exponent,
+        gamma_terms=fdr_cfg.gamma_terms,
+    )
+    assert staging["n_trials_to_date"] == expected_trials
+    assert staging["n_trials_next"] == expected_trials + 1
+    assert staging["next_level"] == expected_level
+
+
+def test_canonical_required_p_uses_the_imported_referee_constant_not_a_literal():
+    """`DEFAULT_ALPHA_PER_TEST` must be `app.engine.referee`'s own constant (0.05 today) -- the module
+    imports it rather than hard-coding "0.05" anywhere (anti-goal: No magic numbers)."""
+    assert DEFAULT_ALPHA_PER_TEST == 0.05
+    assert DEFAULT_ALPHA_BUDGET == 1.0
+
+
+def test_real_ledgers_today_seven_trials_each_status_derived():
+    """Grounds the single-source tests in the documented plateau state (goal.md's Evidence-frontier
+    plateau note) -- status-derived from the real files, not a bare hardcoded assumption."""
+    payload = build_budget_payload()
+    assert payload["canonical"]["n_trials_to_date"] == count_trials(str(_CANONICAL_LEDGER))
+    assert payload["staging"]["n_trials_to_date"] == count_trials(str(_STAGING_LEDGER))
+
+
+def test_real_ledger_spend_over_time_all_fail_today_matches_plateau_note():
+    """goal.md's Evidence-frontier plateau note: 7/7 canonical + 7/7 staging verdicts FAIL today."""
+    payload = build_budget_payload()
+    assert len(payload["canonical"]["spend_over_time"]) == 7
+    assert all(p["status"] == "FAIL" for p in payload["canonical"]["spend_over_time"])
+    assert len(payload["staging"]["spend_over_time"]) == 7
+    assert all(p["status"] == "FAIL" for p in payload["staging"]["spend_over_time"])
+
+
+# ==================================================================================================
+# Fixture-spend: a THROWAWAY tmp_path ledger, hand-computed figures, real ledgers never written
+# ==================================================================================================
+def test_fixture_spend_canonical_trial_count_and_required_p_move_exactly(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    missing_staging = str(tmp_path / "nope-staging.jsonl")
+    for i in range(3):
+        append_entry(str(canonical), _entry(f"f{i}", horizon=20 + i))
+    before = build_budget_payload(canonical_path=str(canonical), staging_path=missing_staging)
+    assert before["canonical"]["n_trials_to_date"] == 3
+    assert before["canonical"]["n_trials_next"] == 4
+    assert before["canonical"]["required_p"] == DEFAULT_ALPHA_PER_TEST / 4
+
+    append_entry(str(canonical), _entry("f3", horizon=99))
+    after = build_budget_payload(canonical_path=str(canonical), staging_path=missing_staging)
+    assert after["canonical"]["n_trials_to_date"] == 4
+    assert after["canonical"]["n_trials_next"] == 5
+    assert after["canonical"]["required_p"] == DEFAULT_ALPHA_PER_TEST / 5
+
+
+def test_fixture_spend_stable_vs_overfit_alpha_charged(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _entry("stable", alpha_charged=0.0))
+    append_entry(str(canonical), _entry("overfit", alpha_charged=0.05))
+    payload = build_budget_payload(
+        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    assert payload["canonical"]["alpha_spent"] == 0.05
+    assert payload["canonical"]["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET - 0.05
+    charges = [p["alpha_charged"] for p in payload["canonical"]["spend_over_time"]]
+    assert charges == [0.0, 0.05]
+
+
+def test_fixture_spend_staging_level_recomputes_per_lord_plusplus(tmp_path):
+    staging = tmp_path / "staging.jsonl"
+    fdr_cfg = get_config().evidence.fdr
+    for i in range(2):
+        append_entry(str(staging), _entry(f"s{i}", horizon=20 + i, deflation="lord++"))
+    payload = build_budget_payload(
+        canonical_path=str(tmp_path / "nope-canonical.jsonl"), staging_path=str(staging),
+    )
+    expected = online_fdr.test_level(
+        3, [], alpha=fdr_cfg.alpha, w0_fraction=fdr_cfg.w0_fraction,
+        gamma_exponent=fdr_cfg.gamma_exponent, gamma_terms=fdr_cfg.gamma_terms,
+    )
+    assert payload["staging"]["next_level"] == expected
+    assert payload["staging"]["n_trials_next"] == 3
+
+
+def test_fixture_spend_series_carries_required_p_and_deflation_divisor_verbatim(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _entry("f0", required_p=0.05, deflation_divisor=1))
+    append_entry(str(canonical), _entry("f1", required_p=0.025, deflation_divisor=2))
+    payload = build_budget_payload(
+        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    points = payload["canonical"]["spend_over_time"]
+    assert [p["required_p"] for p in points] == [0.05, 0.025]
+    assert [p["deflation_divisor"] for p in points] == [1, 2]
+    assert [p["trial"] for p in points] == [1, 2]
+
+
+def test_fixture_spend_never_writes_the_real_ledgers(tmp_path):
+    canonical_before = _CANONICAL_LEDGER.read_text(encoding="utf-8")
+    staging_before = _STAGING_LEDGER.read_text(encoding="utf-8")
+    # Exercise the module against a throwaway ledger only.
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _entry("f0"))
+    build_budget_payload(canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"))
+    # And against the real files, read-only -- still no mutation.
+    build_budget_payload(canonical_path=str(_CANONICAL_LEDGER), staging_path=str(_STAGING_LEDGER))
+    assert _CANONICAL_LEDGER.read_text(encoding="utf-8") == canonical_before
+    assert _STAGING_LEDGER.read_text(encoding="utf-8") == staging_before
+
+
+# ==================================================================================================
+# Resilience: missing/empty ledger -> honest snapshot; all-FAIL -> no replenishment; series length
+# ==================================================================================================
+def test_missing_ledgers_degrade_to_honest_empty_snapshot_no_crash(tmp_path):
+    payload = build_budget_payload(
+        canonical_path=str(tmp_path / "nope-canonical.jsonl"),
+        staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    canonical = payload["canonical"]
+    assert canonical["n_trials_to_date"] == 0
+    assert canonical["n_trials_next"] == 1
+    assert canonical["required_p"] == DEFAULT_ALPHA_PER_TEST / 1
+    assert canonical["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET
+    assert canonical["spend_over_time"] == []
+    staging = payload["staging"]
+    assert staging["n_trials_to_date"] == 0
+    assert staging["n_trials_next"] == 1
+    assert staging["spend_over_time"] == []
+    assert staging["next_level"] > 0  # the staging economy's initial wealth -- finite, never a crash
+
+
+def test_empty_ledger_files_degrade_to_honest_empty_snapshot_no_crash(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    canonical.write_text("", encoding="utf-8")
+    staging = tmp_path / "staging.jsonl"
+    staging.write_text("", encoding="utf-8")
+    payload = build_budget_payload(canonical_path=str(canonical), staging_path=str(staging))
+    assert payload["canonical"]["n_trials_to_date"] == 0
+    assert payload["staging"]["n_trials_to_date"] == 0
+
+
+def test_all_fail_ledger_staging_next_level_depletes_no_replenishment(tmp_path):
+    """No PASS ever -> `rejection_offsets` is always empty -> the staging next-trial level keeps
+    shrinking trial over trial (no replenishment), never climbing back up."""
+    staging = tmp_path / "staging.jsonl"
+    levels = []
+    for i in range(5):
+        append_entry(str(staging), _entry(f"f{i}", horizon=20 + i, deflation="lord++"))
+        payload = build_budget_payload(
+            canonical_path=str(tmp_path / "nope-canonical.jsonl"), staging_path=str(staging),
+        )
+        levels.append(payload["staging"]["next_level"])
+    for earlier, later in zip(levels, levels[1:]):
+        assert later < earlier
+
+
+def test_spend_over_time_length_equals_count_trials_fixture(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    for i in range(4):
+        append_entry(str(canonical), _entry(f"f{i}", horizon=20 + i))
+    payload = build_budget_payload(
+        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    assert len(payload["canonical"]["spend_over_time"]) == count_trials(str(canonical)) == 4
+
+
+def test_forward_walk_entries_excluded_from_trial_count_and_spend_over_time(tmp_path):
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _entry("f0"))
+    forward_walk = _entry("f0", horizon=999)
+    forward_walk["type"] = "forward_walk"
+    append_entry(str(canonical), forward_walk)
+    payload = build_budget_payload(
+        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    assert payload["canonical"]["n_trials_to_date"] == 1
+    assert len(payload["canonical"]["spend_over_time"]) == 1
+
+
+def test_spend_over_time_length_equals_count_trials_real_ledgers():
+    payload = build_budget_payload()
+    assert len(payload["canonical"]["spend_over_time"]) == count_trials(str(_CANONICAL_LEDGER))
+    assert len(payload["staging"]["spend_over_time"]) == count_trials(str(_STAGING_LEDGER))
diff --git a/apps/frontend/app/research/budget/page.tsx b/apps/frontend/app/research/budget/page.tsx
new file mode 100644
index 0000000..dd09b43
--- /dev/null
+++ b/apps/frontend/app/research/budget/page.tsx
@@ -0,0 +1,224 @@
+"use client";
+
+import { useEffect, useState } from "react";
+import Link from "next/link";
+import { AlertTriangle, ArrowLeft } from "lucide-react";
+
+import { useAsOfHref } from "@/components/asof-provider";
+import { PageHeading } from "@/components/page-heading";
+import { Card, CardContent } from "@/components/ui/card";
+import { fetchBudget, type BudgetResponse, type BudgetSpendPoint } from "@/lib/api";
+import { formatPValue } from "@/lib/evidence";
+import { cn } from "@/lib/utils";
+
+/**
+ * /research/budget — the certification-budget accounting panel (goal-mcp-loop iter-32, J-17 / backlog
+ * B-903).
+ *
+ * A read-only view of how much statistical-credibility budget has already been spent, BEFORE any new
+ * scan is proposed: total canonical trials to date, the current canonical `required_p` bar, the
+ * Thresholdout budget remaining, and the staging LORD++ next-trial level — each with a per-trial
+ * spend-over-time trend. Reads ONLY `GET /api/research/budget`, which re-reads (or re-derives via the
+ * SAME referee/ledger seams the certifier uses) the exact accounting `app.mcp.tools:verify_edge`
+ * consumes — nothing is recomputed here. No forms, no mutations.
+ *
+ * NO proven-language anywhere on this page: every figure is descriptive accounting (a trial count, a
+ * significance bar, an alpha budget) — never a "Proven"/"Not yet proven" signal. The single source of
+ * "Proven" stays `/evidence`; this page never resolves or displays evidence status.
+ */
+export default function BudgetPage() {
+  const [state, setState] = useState<State>({ kind: "loading" });
+
+  useEffect(() => {
+    const controller = new AbortController();
+    setState({ kind: "loading" });
+    fetchBudget(controller.signal)
+      .then((data) => setState({ kind: "ok", data }))
+      .catch(() => {
+        if (!controller.signal.aborted) setState({ kind: "error" });
+      });
+    return () => controller.abort();
+  }, []);
+
+  return (
+    <div className="space-y-4">
+      <div className="space-y-2">
+        <BackToResearch />
+        <PageHeading
+          title="Certification-budget accounting"
+          subtitle="How much statistical-credibility budget has already been spent, before any new scan is proposed — re-read from the same referee/ledger accounting the certifier uses. Descriptive accounting only; nothing here is a proven/not-proven signal."
+        />
+      </div>
+
+      {state.kind === "loading" ? <BudgetSkeleton /> : null}
+
+      {state.kind === "error" ? (
+        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
+          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
+          <div>
+            <p className="font-medium">Backend unavailable</p>
+            <p className="text-text-muted">
+              The budget accounting panel could not load from the API. Confirm the backend is running
+              and reload.
+            </p>
+          </div>
+        </Card>
+      ) : null}
+
+      {state.kind === "ok" ? <BudgetGrid data={state.data} /> : null}
+    </div>
+  );
+}
+
+type State = { kind: "loading" } | { kind: "ok"; data: BudgetResponse } | { kind: "error" };
+
+/** A same-window link back to the Research hub (mirrors `research/graveyard/page.tsx`'s pattern exactly). */
+function BackToResearch() {
+  const asofHref = useAsOfHref();
+  return (
+    <Link
+      href={asofHref("/research")}
+      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
+    >
+      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
+    </Link>
+  );
+}
+
+/** Budget figures are always in [0, 1] (a fraction of the starting alpha budget). 4 significant figures
+ *  mirrors `formatPValue`'s own precision (both are bar-like probabilities on this panel), but a budget
+ *  amount can legitimately BE exactly 0 ("fully spent") — so, unlike `formatPValue`, 0 renders as "0",
+ *  never the p-value-style "< 0.0001" wording. Display-only; never recomputed. */
+function formatAlpha(value: number | null | undefined): string {
+  if (value == null || !Number.isFinite(value)) return "—";
+  if (value <= 0) return "0";
+  return Number(value.toPrecision(4)).toString();
+}
+
+function BudgetGrid({ data }: { data: BudgetResponse }) {
+  const { canonical, staging } = data;
+  return (
+    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="budget-grid">
+      <StatCard
+        testId="budget-trials"
+        title="Total trials to date"
+        headline={String(canonical.n_trials_to_date)}
+        subtext={`Next canonical trial will be #${canonical.n_trials_next}`}
+        sparkline={<Sparkline values={canonical.spend_over_time.map((p) => p.trial)} />}
+      />
+      <StatCard
+        testId="budget-required-p"
+        title="Current canonical required p"
+        headline={formatPValue(canonical.required_p)}
+        subtext={`= ${canonical.alpha_per_test} ÷ ${canonical.n_trials_next} (Bonferroni)`}
+        sparkline={<Sparkline values={spendField(canonical.spend_over_time, "required_p")} />}
+      />
+      <StatCard
+        testId="budget-thresholdout-remaining"
+        title="Thresholdout budget remaining"
+        headline={formatAlpha(canonical.alpha_budget_remaining)}
+        subtext={`of ${formatAlpha(canonical.alpha_budget_total)} total · spent ${formatAlpha(canonical.alpha_spent)}`}
+        sparkline={<Sparkline values={spendField(canonical.spend_over_time, "alpha_charged")} />}
+      />
+      <StatCard
+        testId="budget-staging-wealth"
+        title="Staging LORD++ next-trial level"
+        headline={formatPValue(staging.next_level)}
+        subtext={`trial #${staging.n_trials_next} of the internal staging economy`}
+        sparkline={<Sparkline values={spendField(staging.spend_over_time, "required_p")} />}
+      />
+    </div>
+  );
+}
+
+/** Pull one numeric field off a spend-over-time series for the sparkline, defensively skipping any
+ *  point missing that field (never fabricating a 0 in its place). */
+function spendField(points: BudgetSpendPoint[], field: "required_p" | "alpha_charged"): number[] {
+  return points
+    .map((p) => p[field])
+    .filter((v): v is number => typeof v === "number" && Number.isFinite(v));
+}
+
+function StatCard({
+  testId,
+  title,
+  headline,
+  subtext,
+  sparkline,
+}: {
+  testId: string;
+  title: string;
+  headline: string;
+  subtext: string;
+  sparkline: React.ReactNode;
+}) {
+  return (
+    <Card data-testid={testId}>
+      <CardContent className="space-y-3 p-5">
+        <h3 className="text-xs font-medium uppercase tracking-wide text-text-faint">{title}</h3>
+        <p className="num text-2xl font-semibold text-text" data-testid={`${testId}-value`}>
+          {headline}
+        </p>
+        <p className="text-xs text-text-muted">{subtext}</p>
+        {sparkline}
+      </CardContent>
+    </Card>
+  );
+}
+
+/** A compact per-metric spend-over-time mini-trend — an inline SVG sparkline (no charting library; 4
+ *  small series don't warrant one). Pure presentation: `values` are already-fetched, verbatim/re-derived
+ *  server numbers in append order; this only maps them to normalized pixel coordinates for the polyline
+ *  — no new statistic is computed, exactly like any chart library's own internal pixel scaling. An empty
+ *  series (0 trials on that ledger) renders an honest placeholder, never a crash. */
+function Sparkline({ values }: { values: number[] }) {
+  if (values.length === 0) {
+    return (
+      <div className="flex h-8 items-center text-[11px] text-text-faint" data-testid="budget-sparkline-empty">
+        No trials yet
+      </div>
+    );
+  }
+  const width = 120;
+  const height = 32;
+  const min = Math.min(...values);
+  const max = Math.max(...values);
+  const span = max - min || 1; // a flat series (min === max) still renders a level line, never divides by 0
+  const coords = values.map((v, i) => {
+    const x = values.length === 1 ? width / 2 : (i / (values.length - 1)) * width;
+    const y = height - ((v - min) / span) * (height - 4) - 2;
+    return { x, y };
+  });
+  const points = coords.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
+  return (
+    <svg
+      viewBox={`0 0 ${width} ${height}`}
+      className="h-8 w-full text-accent"
+      preserveAspectRatio="none"
+      role="img"
+      aria-label="spend-over-time trend"
+      data-testid="budget-sparkline"
+    >
+      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} />
+      {coords.map(({ x, y }, i) => (
+        <circle key={i} cx={x} cy={y} r={1.5} fill="currentColor" />
+      ))}
+    </svg>
+  );
+}
+
+function BudgetSkeleton() {
+  return (
+    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="budget-skeleton">
+      {Array.from({ length: 4 }).map((_, i) => (
+        <Card key={i} className="p-5">
+          <div className="space-y-3">
+            <div className={cn("h-3 w-24 animate-pulse rounded bg-surface-2")} />
+            <div className={cn("h-7 w-16 animate-pulse rounded bg-surface-2")} />
+            <div className={cn("h-8 w-full animate-pulse rounded bg-surface-2")} />
+          </div>
+        </Card>
+      ))}
+    </div>
+  );
+}
diff --git a/apps/frontend/lib/budget.ts b/apps/frontend/lib/budget.ts
new file mode 100644
index 0000000..6cb8bbf
--- /dev/null
+++ b/apps/frontend/lib/budget.ts
@@ -0,0 +1,53 @@
+/**
+ * Certification-budget accounting types (goal-mcp-loop iter-32, J-17 / backlog B-903).
+ *
+ * Mirrors `lib/graveyard.ts`'s types-only pattern for the SEPARATE `GET /api/research/budget` payload —
+ * how much statistical-credibility budget has already been spent, re-read VERBATIM (or re-derived via
+ * the SAME referee/ledger seams the certifier uses; re-format only — nothing recomputed here).
+ *
+ * This module carries NO proven-language: trial counts and alpha figures are descriptive accounting,
+ * never a "Proven"/"Not yet proven" signal. The ONLY source of "Proven" stays the certified-claims
+ * ledger via `lib/evidence.ts` / `GET /api/evidence`; this file never touches that path.
+ */
+
+/** One point on a ledger's per-trial spend-over-time series, read VERBATIM from that trial's OWN
+ *  recorded verdict (never recomputed). `required_p` is the significance bar (Bonferroni or LORD++)
+ *  that trial was actually judged at; `deflation_divisor` / `alpha_charged` ride along on the canonical
+ *  series only (staging's `deflation_divisor` mirrors the trial ordinal under LORD++, not a meaningful
+ *  divisor, so it is omitted there). */
+export interface BudgetSpendPoint {
+  trial: number;
+  register_date: string | null;
+  status: string | null;
+  required_p: number | null;
+  deflation_divisor?: number | null;
+  alpha_charged?: number | null;
+}
+
+/** The canonical (strict-Bonferroni) accounting: trials to date (a DISPLAY value, distinct from the
+ *  forward-looking `n_trials_next`), the forward next-trial bar, and the Thresholdout budget remaining. */
+export interface CanonicalBudget {
+  n_trials_to_date: number;
+  n_trials_next: number;
+  alpha_per_test: number;
+  required_p: number;
+  alpha_budget_total: number;
+  alpha_spent: number;
+  alpha_budget_remaining: number;
+  spend_over_time: BudgetSpendPoint[];
+}
+
+/** The staging (LORD++) accounting: trials to date, and the forward next-trial significance level (the
+ *  "alpha-wealth" figure) — the internal exploration economy, never served on the canonical /evidence bar. */
+export interface StagingBudget {
+  n_trials_to_date: number;
+  n_trials_next: number;
+  next_level: number;
+  spend_over_time: BudgetSpendPoint[];
+}
+
+/** The `GET /api/research/budget` payload: the canonical + staging accounting, each self-contained. */
+export interface BudgetResponse {
+  canonical: CanonicalBudget;
+  staging: StagingBudget;
+}
```
