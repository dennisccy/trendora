# Iteration diff (bounded)

Files changed: 12. Shown in full: 12.

```diff
diff --git a/README.md b/README.md
index cdd5bcc..399abdc 100644
--- a/README.md
+++ b/README.md
@@ -30,6 +30,7 @@ Current capabilities:
   - **Recovery-Turn Edge** — per-horizon return distribution (mean, median, win rate, expectancy), average max-drawdown, and downside-only risk-adjusted figures broken out by the market phase at each signal date; Episodes/Pooled and All-history/As-of toggles; survivorship-bias disclosure always shown.
   - **Downtrend Opportunity** — groups walk-forward observations by market state (causal phase, drawdown-severity band, or bear-probability band) and shows three ranked tables: "Held up best", "Fell hardest" (labelled research evidence only — no orders), and "Recovery-turn edge by phase". Each table is sortable, every `N=` chip opens exact underlying observations, and the study respects Episodes/Pooled and All-history/As-of toggles. A macro publication-lag disclosure is always shown.
   - All Research pages: every `N=` sample count is a clickable link that opens a drill-down in a new tab — keeping lab selections and scroll position undisturbed — showing exact stored observations; the observations table is sortable and filterable by ticker. From any observation row click the ticker to open that stock's detail page at the snapshot date in a new tab.
+- **Pre-registration registry**: a "Governance & process" section on the Research hub links, in one click, to a dedicated `/research/registry` page listing every trading hypothesis the platform has ever registered or tested — 11 rows today, each showing its exact selectors as compact, readable chips (e.g. `kind=factor`, `factor=vcp_contraction`, `decile=10`, `horizon=60`, `direction=positive`; a multi-leg combination's selectors render as one chip with legs joined by `+`), its economic rationale, registration date, source, and current status in a neutral gray badge — deliberately distinct from the green/red proven/not-proven coloring used on the Evidence page, so this column is never mistaken for a pass/fail signal. Every backfilled historical row carries a small "backfill" pill, and the page shows an honest loading skeleton, a contained error card if the backend is unreachable, or an empty state if the registry is ever empty. The registry is read-only — entries can only be added by the platform itself — and going forward the platform's evidence-certification process refuses to test any new idea that was not already logged here first, closing a common way statistical findings get quietly cherry-picked after the fact.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
 - **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
diff --git a/apps/backend/main.py b/apps/backend/main.py
index 915a6c8..404c521 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -20,6 +20,7 @@ from app.api import (
     dashboard,
     data,
     evidence,
+    graveyard,
     health,
     indexes,
     market_phase,
@@ -133,6 +134,8 @@ def create_app() -> FastAPI:
     application.include_router(evidence.router, prefix="/api")
     # goal-mcp-loop iter-30 (J-18) — the read-only pre-registration registry (GET /api/research/registry).
     application.include_router(registry.router, prefix="/api")
+    # goal-mcp-loop iter-31 (J-19) — the read-only negative-results graveyard (GET /api/research/graveyard).
+    application.include_router(graveyard.router, prefix="/api")
     return application
 
 
diff --git a/apps/backend/tests/test_registry.py b/apps/backend/tests/test_registry.py
index c98aa6f..fd869e5 100644
--- a/apps/backend/tests/test_registry.py
+++ b/apps/backend/tests/test_registry.py
@@ -23,6 +23,7 @@ import json
 from pathlib import Path
 
 from app.config import REPO_ROOT
+from app.engine import registry as registry_mod
 from app.engine.ledger import append_entry, read_entries
 from app.engine.registry import (
     REGISTRY_PATH_ENV,
@@ -31,6 +32,7 @@ from app.engine.registry import (
     match_registration,
     resolve_registry_path,
 )
+from app.mcp import tools as mcp_tools
 
 _CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
 _STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
@@ -280,3 +282,13 @@ def test_committed_registry_has_no_proven_language():
     banned = {"proven", "pass", "confirmed", "verified", "certified"}
     for row in rows:
         assert row["status"].lower() not in banned
+
+
+# ==================================================================================================
+# Drift insurance (iter-30 audit-O1 carry-forward, iter-31 recommended cheap add): the selector-key
+# tuple this module matches on must stay byte-identical to `app.mcp.tools`'s copy -- the graveyard
+# (iter-31, J-19) leans on `match_registration` for lineage, so a silent drift between the two tuples
+# would silently break lineage matching for any claim carrying a key added to one copy but not the other.
+# ==================================================================================================
+def test_claim_selector_keys_matches_mcp_tools_verbatim():
+    assert registry_mod._CLAIM_SELECTOR_KEYS == mcp_tools._CLAIM_SELECTOR_KEYS
diff --git a/apps/frontend/app/research/page.tsx b/apps/frontend/app/research/page.tsx
index 5b599e0..8128453 100644
--- a/apps/frontend/app/research/page.tsx
+++ b/apps/frontend/app/research/page.tsx
@@ -2,6 +2,7 @@
 
 import Link from "next/link";
 import {
+  Archive,
   ArrowRight,
   BookMarked,
   Boxes,
@@ -75,10 +76,10 @@ export default function ResearchHubPage() {
         })}
       </div>
 
-      {/* goal-mcp-loop iter-30 (J-18) — Governance & process: the first of several forthcoming governance
-          surfaces (registry now; graveyard / budget / referee-audit to follow). Kept a SEPARATE section,
-          not an 11th RESEARCH_LABS entry — that array's reading order is a J-113 contract over the ten
-          analytical labs; a governance/process link is architecturally distinct, not a lab. */}
+      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) — Governance & process: registry + graveyard now,
+          budget / referee-audit still to follow. Kept a SEPARATE section, not an 11th RESEARCH_LABS
+          entry — that array's reading order is a J-113 contract over the ten analytical labs; a
+          governance/process link is architecturally distinct, not a lab. */}
       <div className="space-y-3">
         <h2 className="text-sm font-semibold uppercase tracking-wide text-text-faint">Governance &amp; process</h2>
         <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-governance">
@@ -101,6 +102,28 @@ export default function ResearchHubPage() {
               registration date, and source. The gate refuses to certify anything that isn&apos;t here.
             </p>
           </Link>
+
+          {/* goal-mcp-loop iter-31 (J-19) — the negative-results graveyard: every referee-rejected
+              hypothesis across both ledgers, so nobody re-derives a dead idea from scratch. */}
+          <Link
+            href={asofHref("/research/graveyard")}
+            data-testid="research-governance-link-graveyard"
+            className={cn(
+              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
+              "hover:border-accent hover:bg-surface-2",
+              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
+            )}
+          >
+            <div className="flex items-center gap-2">
+              <Archive className="h-5 w-5 text-accent" aria-hidden />
+              <h3 className="text-base font-semibold text-text">Negative-results graveyard</h3>
+              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
+            </div>
+            <p className="text-sm text-text-muted">
+              Every hypothesis the referee has rejected, across the canonical and staging ledgers — its
+              verdict, deflation context, and registration lineage. Nobody retries a dead idea blindly.
+            </p>
+          </Link>
         </div>
       </div>
     </div>
diff --git a/apps/frontend/app/research/registry/page.tsx b/apps/frontend/app/research/registry/page.tsx
index e89472a..a59b824 100644
--- a/apps/frontend/app/research/registry/page.tsx
+++ b/apps/frontend/app/research/registry/page.tsx
@@ -40,6 +40,24 @@ export default function RegistryPage() {
     return () => controller.abort();
   }, []);
 
+  // Scroll to a `#registration-<id>` deep-link target once the rows have rendered. The browser's native
+  // scroll-to-fragment fires only on a full/hard page load; on a client-side (SPA) navigation into this
+  // route — e.g. clicking a graveyard row's Lineage link (goal-mcp-loop iter-31, J-19) — the target row
+  // is fetched AFTER the route commits, so the fragment resolves to nothing and no scroll happens. This
+  // effect runs after the rows mount (`state.kind === "ok"`) and brings the anchored row into view; the
+  // row's `scroll-mt-20` positions it just below the sticky header. No hash ⇒ no-op (plain browsing is
+  // unchanged). rAF defers one frame so layout is settled before scrolling.
+  useEffect(() => {
+    if (state.kind !== "ok") return;
+    const hash = window.location.hash;
+    if (!hash) return;
+    const raf = requestAnimationFrame(() => {
+      const target = document.getElementById(hash.slice(1));
+      if (target) target.scrollIntoView({ block: "start" });
+    });
+    return () => cancelAnimationFrame(raf);
+  }, [state.kind]);
+
   const rows = state.kind === "ok" ? state.data.registrations : [];
 
   return (
@@ -128,7 +146,12 @@ function RegistryTable({ rows }: { rows: PreRegistrationRow[] }) {
           </thead>
           <tbody>
             {rows.map((row) => (
-              <tr key={row.id} data-testid="registry-row" className="border-b border-border align-top last:border-b-0">
+              <tr
+                key={row.id}
+                id={`registration-${row.id}`}
+                data-testid="registry-row"
+                className="scroll-mt-20 border-b border-border align-top last:border-b-0"
+              >
                 <td className="px-4 py-3">
                   <SelectorChips selectors={row.selectors} />
                 </td>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 4a07403..acee670 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -11,6 +11,7 @@ import type {
   EvidenceLedgerResponse,
   ProvenSignal,
 } from "@/lib/evidence";
+import type { GraveyardEntry, GraveyardResponse, RevisitProtocol } from "@/lib/graveyard";
 import type { PreRegistrationRow, RegistryResponse } from "@/lib/registry";
 
 // Re-export the read-side evidence types (goal-mcp-loop iter-1) so callers import them from the API client
@@ -21,6 +22,9 @@ export type { CertifiedClaim, EvidenceLedgerResponse, ProvenSignal };
 // Re-export the pre-registration registry types (goal-mcp-loop iter-30, J-18) alongside `fetchRegistry`.
 export type { PreRegistrationRow, RegistryResponse };
 
+// Re-export the negative-results graveyard types (goal-mcp-loop iter-31, J-19) alongside `fetchGraveyard`.
+export type { GraveyardEntry, GraveyardResponse, RevisitProtocol };
+
 /** The build-time configured backend base (`NEXT_PUBLIC_API_URL`, default localhost). The configured
  *  backend PORT (`NEXT_PUBLIC_API_PORT`) is read alongside so the runtime resolver can host-swap to the
  *  page's own host when the page is opened at a non-localhost (LAN-IP) origin (J-108). Both are inlined
@@ -362,6 +366,16 @@ export async function fetchRegistry(signal?: AbortSignal): Promise<RegistryRespo
   return getJSON<RegistryResponse>("/api/research/registry", signal);
 }
 
+// --- negative-results graveyard (goal-mcp-loop iter-31, J-19 / backlog B-902) ---------------
+/** GET /api/research/graveyard — the read-only negative-results graveyard: every NON-PASS referee
+ *  verdict across BOTH the canonical and staging certified-claims ledgers, read VERBATIM and tagged with
+ *  its origin ledger + registration lineage. Re-formats nothing; introduces no proven-language (a
+ *  verdict-kind badge, never "Proven"/"Not yet proven"). Throws on network error or non-200 so the page
+ *  renders an explicit "Backend unavailable" state. */
+export async function fetchGraveyard(signal?: AbortSignal): Promise<GraveyardResponse> {
+  return getJSON<GraveyardResponse>("/api/research/graveyard", signal);
+}
+
 // --- stock price/MA/volume series for the detail chart (iter-4) -----------------------------
 /** One ascending OHLCV bar. By default date <= as-of (no lookahead — the backend reads only
  *  `bars_asof`). With the J-20 `through=latest` opt-in the series extends through the latest seed bar
diff --git a/apps/backend/app/api/graveyard.py b/apps/backend/app/api/graveyard.py
new file mode 100644
index 0000000..bd92267
--- /dev/null
+++ b/apps/backend/app/api/graveyard.py
@@ -0,0 +1,31 @@
+"""GET /api/research/graveyard — the read-only negative-results graveyard surface (goal-mcp-loop iter-31,
+J-19 / backlog B-902).
+
+Serves `app.engine.graveyard.build_graveyard_payload` verbatim (re-format only — no recompute): every
+NON-PASS referee verdict across BOTH the canonical and staging certified-claims ledgers, each tagged with
+its origin ledger and joined to its registration lineage, plus the served `revisit_protocol` constant.
+
+No DB/session is needed (both ledgers are append-only state files, not the snapshot DB). Ledger paths are
+config/env-driven via the resolvers (anti-goal: No magic numbers — no path literal here). A missing/empty
+ledger (either or both) returns 200 with an empty entries list, never a 500 (anti-goal: resilience to
+data-shape change).
+
+READ-ONLY, always: this module carries no deletion/edit path for any entry (append-only history), and no
+proven-language — a verdict-kind (FAIL/INSUFFICIENT) is descriptive, never a "Proven"/"Not yet proven"
+signal. That continues to flow solely from `app.engine.evidence` / `GET /api/evidence`, untouched here.
+"""
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.engine.graveyard import build_graveyard_payload
+
+router = APIRouter(tags=["graveyard"])
+
+
+@router.get("/research/graveyard")
+def get_graveyard() -> dict:
+    """Every NON-PASS referee verdict across both ledgers, verbatim, tagged by origin ledger and
+    lineage-attached: `{"entries": [...], "revisit_protocol": {...}}`. READ-ONLY — recomputes nothing. A
+    missing/empty ledger (either or both) ⇒ fewer/zero entries (200, never 500)."""
+    return build_graveyard_payload()
diff --git a/apps/backend/app/engine/graveyard.py b/apps/backend/app/engine/graveyard.py
new file mode 100644
index 0000000..0788ea8
--- /dev/null
+++ b/apps/backend/app/engine/graveyard.py
@@ -0,0 +1,137 @@
+"""The negative-results graveyard — the read-side composition of every NON-PASS referee verdict across
+BOTH the canonical and staging certified-claims ledgers (goal-mcp-loop iter-31, J-19 / backlog B-902).
+
+This module is the institutional-memory companion to `app.engine.evidence` ("what is proven") and
+`app.engine.registry` ("what is registered"): it answers "what does NOT work", so a future model — or the
+owner in month 9 — never re-derives a dead hypothesis from scratch. It is a PURE, engine-free read-compose
+module (mirrors `app.engine.registry`'s shape): filesystem read + dict work only, no DB session, no
+computation. It RECOMPUTES NOTHING — every verdict field is re-displayed exactly as the referee wrote it.
+
+  - `resolve_staging_ledger_path()` — the staging ledger's path: the `STAGING_LEDGER_PATH` env override
+    (the SAME literal name `run-goal.sh` already exports and `project-extensions/gates/verify_claim.py`
+    already reads — deliberately NOT a new `TRENDORA_STAGING_LEDGER_PATH` name), else
+    `config.evidence.staging_ledger_path` resolved against `REPO_ROOT`. Mirrors
+    `app.engine.evidence.resolve_ledger_path()` exactly, for the staging side.
+  - `build_graveyard_payload()` — reads BOTH ledgers (canonical via the EXISTING
+    `app.engine.evidence.resolve_ledger_path()`; staging via `resolve_staging_ledger_path()` above),
+    excludes forward-walk monitoring records, filters to NON-PASS verdicts (`FAIL` / `INSUFFICIENT`,
+    status-driven — never a hardcoded count), tags each entry with its origin ledger, re-displays the
+    deflation context (`verdict.deflation` / `verdict.deflation_divisor`) verbatim, and attaches
+    registration lineage via the SAME `app.engine.registry.match_registration` the J-18 gate/registry-page
+    use (reused, never reimplemented — a second selector-matcher is the exact failure mode B-902 calls
+    out). A missing/empty ledger degrades to an empty graveyard, never a crash.
+  - `REVISIT_PROTOCOL` — a single served constant (the B-406/§0 rule text) so every page/consumer reads
+    the SAME re-test policy; carries no proven-language.
+
+One deliberate contract evolution (logged in the iter-31 blueprint clarification): the iter-9/10/12
+"staging ledger is internal-only, never served" invariant is NARROWED here — the staging ledger's NON-PASS
+verdicts become browsable (the graveyard's whole purpose). The honesty fence stays intact: this module
+shows ONLY non-PASS entries (staging carries 0 PASS rows today, and even if it ever did, a PASS entry is
+filtered OUT here, never surfaced as proven), and it never touches `app.engine.evidence`,
+`build_evidence_payload`, `proven_signals`, or either ledger's write path — read-only, always.
+"""
+from __future__ import annotations
+
+import os
+from pathlib import Path
+
+from app.config import REPO_ROOT, get_config
+from app.engine import evidence as evidence_mod
+from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
+from app.engine.referee import STATUS_PASS
+from app.engine.registry import load_registrations, match_registration
+
+# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime staging
+# ledger path may be overridden with. The SAME literal `run-goal.sh` exports and `verify_claim.py` reads
+# (project-extensions/gates/verify_claim.py `_LEDGER_ENV["staging"]`) — deliberately reused rather than a
+# new `TRENDORA_STAGING_LEDGER_PATH` name, since the harness never sets one.
+STAGING_LEDGER_PATH_ENV = "STAGING_LEDGER_PATH"
+
+# The two ledger-origin tags a graveyard entry may carry. Local literals (not imported from `app.mcp.tools`,
+# which sits above the engine layer) — mirrors how `app.engine.ledger._PASS_STATUS` mirrors
+# `app.engine.referee.STATUS_PASS` "so this module stays engine-free."
+LEDGER_CANONICAL = "canonical"
+LEDGER_STAGING = "staging"
+
+# The re-test policy (backlog B-406 / §0), served as a single constant so every consumer (the graveyard
+# page's panel, any future reader) agrees on the SAME wording. Descriptive governance text — NO
+# proven-language (this is never a "Proven"/"Not yet proven" signal).
+REVISIT_PROTOCOL: dict = {
+    "rule": (
+        "A referee FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a materially "
+        "changed precondition (a new data span covering ≥2 additional OOS years, a data-basis "
+        "change, or a genuinely different hypothesis) and must be registered as a NEW candidate citing "
+        "the closed verdict."
+    ),
+}
+
+
+def resolve_staging_ledger_path() -> str:
+    """The staging ledger path: the `STAGING_LEDGER_PATH` env override if set, else
+    `config.evidence.staging_ledger_path` resolved against `REPO_ROOT` when relative.
+
+    This MUST resolve to the SAME file the post-decompose gate writes staging verdicts to (set by
+    `run-goal.sh` alongside `LEDGER_PATH`/`TRENDORA_REGISTRY_PATH`), so the graveyard's staging rows are
+    consistent with what the referee actually explored. No path literal lives here — the default lives in
+    config (anti-goal: No magic numbers). Mirrors `app.engine.evidence.resolve_ledger_path()` exactly."""
+    override = os.environ.get(STAGING_LEDGER_PATH_ENV)
+    if override:
+        return override
+    configured = Path(get_config().evidence.staging_ledger_path)
+    if not configured.is_absolute():
+        configured = REPO_ROOT / configured
+    return str(configured)
+
+
+def _graveyard_row(entry: dict, ledger: str, registrations: list[dict]) -> dict:
+    """Project ONE non-PASS ledger entry into a read-only graveyard row — read VERBATIM (nothing is
+    recomputed). `lineage` is the matched registry row (or `None` for an honest unregistered selector-set),
+    resolved via the SAME `registry.match_registration` the gate/registry-page use."""
+    claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
+    verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
+    return {
+        "ledger": ledger,
+        "claim": claim,                                    # the hypothesis (cohort selectors), verbatim
+        "register_date": entry.get("register_date"),
+        "horizon": entry.get("horizon"),
+        "cohort_n": entry.get("cohort_n"),
+        "control_n": entry.get("control_n"),
+        "verdict": verdict,                                # status + reason + deflation context, verbatim
+        "lineage": match_registration(claim, registrations=registrations),
+    }
+
+
+def _non_pass_rows(ledger_path: str, ledger: str, registrations: list[dict]) -> list[dict]:
+    """Every NON-PASS, non-forward-walk entry in `ledger_path`, tagged `ledger` and lineage-attached.
+    Status-driven (`verdict.status != PASS`), never a hardcoded count — a future PASS row disappears from
+    this list automatically. A missing/empty file yields `read_entries`' own empty list (no crash)."""
+    rows: list[dict] = []
+    for entry in read_entries(ledger_path):
+        if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
+            continue
+        verdict = entry.get("verdict") if isinstance(entry.get("verdict"), dict) else {}
+        if verdict.get("status") == STATUS_PASS:
+            continue
+        rows.append(_graveyard_row(entry, ledger, registrations))
+    return rows
+
+
+def build_graveyard_payload(canonical_path: str | None = None, staging_path: str | None = None) -> dict:
+    """Compose the read-only `/api/research/graveyard` payload: `{"entries": [...], "revisit_protocol":
+    {...}}`. `canonical_path` defaults to `app.engine.evidence.resolve_ledger_path()`; `staging_path`
+    defaults to `resolve_staging_ledger_path()` — the endpoint's real, no-argument call shape. A test may
+    pass explicit fixture paths instead (mirrors `app.engine.registry.load_registrations`'s optional-path
+    pattern).
+
+    `entries` is every NON-PASS (`FAIL` / `INSUFFICIENT`) entry from BOTH ledgers, forward-walk monitoring
+    records excluded, each tagged with its origin ledger and lineage-attached via the SAME
+    `registry.match_registration` the gate/registry-page use (loaded ONCE here and passed through, so a
+    14-row graveyard does not re-read the registry file per entry). A missing/empty ledger (either or both)
+    degrades to fewer/zero entries, never a crash (anti-goal: resilience to data-shape change)."""
+    resolved_canonical = canonical_path if canonical_path is not None else evidence_mod.resolve_ledger_path()
+    resolved_staging = staging_path if staging_path is not None else resolve_staging_ledger_path()
+    registrations = load_registrations()
+    entries = _non_pass_rows(resolved_canonical, LEDGER_CANONICAL, registrations) + _non_pass_rows(
+        resolved_staging, LEDGER_STAGING, registrations
+    )
+    return {"entries": entries, "revisit_protocol": REVISIT_PROTOCOL}
diff --git a/apps/backend/tests/test_api_graveyard.py b/apps/backend/tests/test_api_graveyard.py
new file mode 100644
index 0000000..1356319
--- /dev/null
+++ b/apps/backend/tests/test_api_graveyard.py
@@ -0,0 +1,102 @@
+"""GET /api/research/graveyard API tests (goal-mcp-loop iter-31, J-19 / backlog B-902).
+
+Mounts ONLY the graveyard router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and
+NO walk-forward boot -- the endpoint reads the two append-only ledger state files, not a snapshot
+(mirrors `test_api_registry.py`'s DB-free pattern exactly).
+"""
+from __future__ import annotations
+
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+
+from app.api import graveyard
+from app.engine.evidence import LEDGER_PATH_ENV
+from app.engine.graveyard import (
+    LEDGER_CANONICAL,
+    LEDGER_STAGING,
+    STAGING_LEDGER_PATH_ENV,
+    build_graveyard_payload,
+)
+from app.engine.ledger import append_entry, read_entries
+from app.engine.registry import REGISTRY_PATH_ENV
+
+
+def _client() -> TestClient:
+    app = FastAPI()
+    app.include_router(graveyard.router, prefix="/api")
+    return TestClient(app)
+
+
+def test_graveyard_endpoint_200_empty_on_missing_ledger_files(tmp_path, monkeypatch):
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing-canonical.jsonl"))
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
+    with _client() as client:
+        resp = client.get("/api/research/graveyard")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["entries"] == []
+    assert "revisit_protocol" in body
+
+
+def test_graveyard_endpoint_serves_a_fixture_entry_verbatim(tmp_path, monkeypatch):
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    canonical = tmp_path / "canonical.jsonl"
+    entry = {
+        "claim": {
+            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+            "horizon": 60, "direction": "positive",
+        },
+        "cohort_n": 100, "control_n": 50, "horizon": 60, "register_date": "2026-07-03",
+        "verdict": {
+            "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 3,
+        },
+    }
+    append_entry(str(canonical), entry)
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(canonical))
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
+    with _client() as client:
+        resp = client.get("/api/research/graveyard")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert len(body["entries"]) == 1
+    served = body["entries"][0]
+    assert served["ledger"] == LEDGER_CANONICAL
+    assert served["claim"] == entry["claim"]
+    assert served["verdict"] == entry["verdict"]
+    assert served["register_date"] == entry["register_date"]
+    assert served["horizon"] == entry["horizon"]
+    assert served["cohort_n"] == entry["cohort_n"]
+    assert served["control_n"] == entry["control_n"]
+
+
+def test_graveyard_endpoint_equals_build_graveyard_payload_directly(monkeypatch):
+    """Single-source assertion: the endpoint's response equals `build_graveyard_payload()` called
+    directly against the SAME (real, committed) ledger files -- the page can never disagree with the
+    composition module."""
+    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    with _client() as client:
+        resp = client.get("/api/research/graveyard")
+    assert resp.status_code == 200
+    assert resp.json() == build_graveyard_payload()
+
+
+def test_graveyard_endpoint_real_ledgers_today_serve_fourteen_non_pass_entries(monkeypatch):
+    """Status-derived, not a hardcoded literal (iter-30 lesson): the expected count is COMPUTED from the
+    two real committed ledger files' own non-PASS rows, not asserted as a bare "14"."""
+    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    from app.engine.evidence import resolve_ledger_path
+    from app.engine.graveyard import resolve_staging_ledger_path
+
+    canonical_raw = [e for e in read_entries(resolve_ledger_path()) if e.get("type") != "forward_walk"]
+    staging_raw = [e for e in read_entries(resolve_staging_ledger_path()) if e.get("type") != "forward_walk"]
+    expected = sum(1 for e in canonical_raw + staging_raw if e["verdict"]["status"] != "PASS")
+
+    with _client() as client:
+        resp = client.get("/api/research/graveyard")
+    body = resp.json()
+    assert len(body["entries"]) == expected
+    assert {e["ledger"] for e in body["entries"]} <= {LEDGER_CANONICAL, LEDGER_STAGING}
diff --git a/apps/backend/tests/test_graveyard.py b/apps/backend/tests/test_graveyard.py
new file mode 100644
index 0000000..9805c0c
--- /dev/null
+++ b/apps/backend/tests/test_graveyard.py
@@ -0,0 +1,290 @@
+"""Negative-results graveyard composition tests (goal-mcp-loop iter-31, J-19 / backlog B-902).
+
+`app.engine.graveyard` is a PURE read-compose module: it reads BOTH the canonical and staging
+certified-claims ledgers via the existing `app.engine.ledger.read_entries`, filters to NON-PASS
+verdicts, tags each with its origin ledger, and attaches registration lineage via the EXISTING
+`app.engine.registry.match_registration` (never a second matcher). These tests pin:
+
+  - `resolve_staging_ledger_path` honors the `STAGING_LEDGER_PATH` env override (the SAME literal name
+    `run-goal.sh` / `verify_claim.py` already use), else the config default (mirrors
+    `test_registry.py`'s `resolve_registry_path` tests exactly).
+  - `build_graveyard_payload` over fixture ledgers: non-PASS filter (a PASS fixture entry is excluded),
+    forward-walk exclusion, ledger-origin tag + `deflation`/`deflation_divisor` re-displayed verbatim,
+    lineage attachment via a REAL `match_registration` call (a matched row + an honest `None` for an
+    unregistered selector-set), a "closed" status surfaced verbatim on a matched row, and a missing/empty
+    ledger file (or both) degrading to an empty payload — never a crash.
+  - The REVISIT_PROTOCOL constant is served alongside the entries and carries no proven-language.
+  - At least one REAL committed ledger line (`ma_stack`, the one permanently-closed hypothesis) round-trips
+    end-to-end through the payload (anti-goal #3 proof — not just a synthetic fixture).
+"""
+from __future__ import annotations
+
+from pathlib import Path
+
+from app.config import REPO_ROOT
+from app.engine.graveyard import (
+    LEDGER_CANONICAL,
+    LEDGER_STAGING,
+    REVISIT_PROTOCOL,
+    STAGING_LEDGER_PATH_ENV,
+    build_graveyard_payload,
+    resolve_staging_ledger_path,
+)
+from app.engine.ledger import append_entry, read_entries
+from app.engine.registry import REGISTRY_PATH_ENV
+
+_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
+_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
+
+
+# ==================================================================================================
+# resolve_staging_ledger_path — env override (STAGING_LEDGER_PATH), else config default
+# ==================================================================================================
+def test_resolve_staging_ledger_path_env_override(tmp_path, monkeypatch):
+    override = tmp_path / "override-staging.jsonl"
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(override))
+    assert resolve_staging_ledger_path() == str(override)
+
+
+def test_resolve_staging_ledger_path_config_default(monkeypatch):
+    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
+    resolved = resolve_staging_ledger_path()
+    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl")
+    assert Path(resolved).is_absolute()
+
+
+def test_staging_ledger_path_env_name_matches_the_harness_literal():
+    """The harness (run-goal.sh / verify_claim.py) already exports/reads `STAGING_LEDGER_PATH` — this
+    module MUST honor the same literal name, never a new `TRENDORA_STAGING_LEDGER_PATH`."""
+    assert STAGING_LEDGER_PATH_ENV == "STAGING_LEDGER_PATH"
+
+
+# ==================================================================================================
+# build_graveyard_payload — fixture ledgers: filter / exclusion / tagging / lineage / degrade-empty
+# ==================================================================================================
+_FIXTURE_REGISTRY = [
+    {
+        "id": "factor-vcp_contraction-d10-h60",
+        "selectors": {
+            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
+            "horizon": 60, "direction": "positive",
+        },
+        "rationale": "fixture rationale", "registered_by": "backfill", "registered_date": "2026-07-03",
+        "source": "fixture", "status": "tested",
+    },
+    {
+        "id": "factor-ma_stack-d10-h20",
+        "selectors": {
+            "kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10,
+            "horizon": 20, "direction": "positive",
+        },
+        "rationale": "fixture rationale (closed)", "registered_by": "backfill",
+        "registered_date": "2026-07-03", "source": "fixture", "status": "closed",
+    },
+]
+
+
+def _write_registry(tmp_path, monkeypatch, rows=_FIXTURE_REGISTRY):
+    path = tmp_path / "registry.jsonl"
+    for row in rows:
+        append_entry(str(path), row)
+    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
+    return path
+
+
+def _fail_entry(factor: str, decile: int = 10, horizon: int = 60, **verdict_extra) -> dict:
+    verdict = {
+        "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 3,
+        "holdout_edge": -0.01, "control_excess": -0.01, "p_value": 0.9,
+    }
+    verdict.update(verdict_extra)
+    return {
+        "claim": {
+            "kind": "factor", "factor": factor, "slice_kind": "decile", "decile": decile,
+            "horizon": horizon, "direction": "positive",
+        },
+        "cohort_n": 100, "control_n": 50, "horizon": horizon, "register_date": "2026-07-03",
+        "verdict": verdict,
+    }
+
+
+def test_non_pass_filter_excludes_a_pass_entry(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("vcp_contraction"))
+    pass_entry = _fail_entry("vcp_contraction", horizon=61)
+    pass_entry["verdict"]["status"] = "PASS"
+    append_entry(str(canonical), pass_entry)
+    staging = tmp_path / "staging.jsonl"  # missing/empty is fine for this assertion
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    assert len(payload["entries"]) == 1
+    assert payload["entries"][0]["verdict"]["status"] == "FAIL"
+
+
+def test_insufficient_entry_is_included_non_pass(tmp_path, monkeypatch):
+    """INSUFFICIENT is a non-PASS verdict too -- the filter is `!= PASS`, not `== FAIL`."""
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    entry = _fail_entry("vcp_contraction")
+    entry["verdict"]["status"] = "INSUFFICIENT"
+    append_entry(str(canonical), entry)
+    staging = tmp_path / "staging.jsonl"
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    assert len(payload["entries"]) == 1
+    assert payload["entries"][0]["verdict"]["status"] == "INSUFFICIENT"
+
+
+def test_forward_walk_records_are_excluded(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("vcp_contraction"))
+    forward_walk = _fail_entry("vcp_contraction", horizon=61)
+    forward_walk["type"] = "forward_walk"
+    append_entry(str(canonical), forward_walk)
+    staging = tmp_path / "staging.jsonl"
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    assert len(payload["entries"]) == 1
+    assert payload["entries"][0]["horizon"] == 60  # the original entry, not the horizon=61 forward-walk
+
+
+def test_ledger_origin_tag_and_deflation_fields_reexposed_verbatim(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("vcp_contraction", deflation="bonferroni", deflation_divisor=3))
+    staging = tmp_path / "staging.jsonl"
+    append_entry(str(staging), _fail_entry("vcp_contraction", horizon=10, deflation="lord++", deflation_divisor=1))
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    by_ledger = {e["ledger"]: e for e in payload["entries"]}
+    assert by_ledger[LEDGER_CANONICAL]["verdict"]["deflation"] == "bonferroni"
+    assert by_ledger[LEDGER_CANONICAL]["verdict"]["deflation_divisor"] == 3
+    assert by_ledger[LEDGER_STAGING]["verdict"]["deflation"] == "lord++"
+    assert by_ledger[LEDGER_STAGING]["verdict"]["deflation_divisor"] == 1
+
+
+def test_lineage_attached_via_real_match_registration_for_a_matched_claim(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("vcp_contraction", decile=10, horizon=60))
+    staging = tmp_path / "staging.jsonl"
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    entry = payload["entries"][0]
+    assert entry["lineage"] is not None
+    assert entry["lineage"]["id"] == "factor-vcp_contraction-d10-h60"
+
+
+def test_lineage_is_honest_none_for_an_unregistered_selector_set(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("some_never_registered_factor", decile=7, horizon=5))
+    staging = tmp_path / "staging.jsonl"
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    entry = payload["entries"][0]
+    assert entry["lineage"] is None  # no crash, no fabricated link
+
+
+def test_closed_status_surfaced_verbatim_on_a_matched_row(tmp_path, monkeypatch):
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("ma_stack", decile=10, horizon=20))
+    staging = tmp_path / "staging.jsonl"
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    entry = payload["entries"][0]
+    assert entry["lineage"]["status"] == "closed"
+
+
+def test_missing_ledger_files_degrade_to_empty_payload_no_crash(tmp_path, monkeypatch):
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    payload = build_graveyard_payload(
+        canonical_path=str(tmp_path / "nope-canonical.jsonl"),
+        staging_path=str(tmp_path / "nope-staging.jsonl"),
+    )
+    assert payload["entries"] == []
+    assert payload["revisit_protocol"] == REVISIT_PROTOCOL
+
+
+def test_empty_ledger_files_degrade_to_empty_payload_no_crash(tmp_path, monkeypatch):
+    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
+    canonical = tmp_path / "canonical.jsonl"
+    canonical.write_text("", encoding="utf-8")
+    staging = tmp_path / "staging.jsonl"
+    staging.write_text("", encoding="utf-8")
+    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
+    assert payload["entries"] == []
+
+
+def test_build_graveyard_payload_defaults_to_the_resolvers(tmp_path, monkeypatch):
+    """With BOTH path args omitted, resolution goes through `evidence.resolve_ledger_path()` (canonical)
+    and `resolve_staging_ledger_path()` (staging) -- the endpoint's real, no-argument call shape."""
+    from app.engine import evidence as evidence_mod
+
+    _write_registry(tmp_path, monkeypatch)
+    canonical = tmp_path / "canonical.jsonl"
+    append_entry(str(canonical), _fail_entry("vcp_contraction"))
+    monkeypatch.setenv(evidence_mod.LEDGER_PATH_ENV, str(canonical))
+    staging = tmp_path / "staging.jsonl"
+    append_entry(str(staging), _fail_entry("vcp_contraction", horizon=10))
+    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(staging))
+    payload = build_graveyard_payload()
+    assert len(payload["entries"]) == 2
+    assert {e["ledger"] for e in payload["entries"]} == {LEDGER_CANONICAL, LEDGER_STAGING}
+
+
+# ==================================================================================================
+# REVISIT_PROTOCOL — a single served constant, no proven-language
+# ==================================================================================================
+def test_revisit_protocol_has_no_proven_language():
+    banned = {"proven", "pass", "confirmed", "verified", "certified"}
+    rule_text = REVISIT_PROTOCOL.get("rule", "").lower()
+    for word in banned:
+        assert word not in rule_text, f"revisit-protocol rule text leaked proven-language: {word!r}"
+
+
+def test_revisit_protocol_states_final_and_materially_changed_precondition():
+    rule_text = REVISIT_PROTOCOL.get("rule", "")
+    assert "final" in rule_text.lower()
+    assert "materially changed" in rule_text.lower()
+    assert "NEW candidate" in rule_text or "new candidate" in rule_text.lower()
+
+
+# ==================================================================================================
+# Real-data round-trip (anti-goal #3 proof) — the committed ma_stack FAIL, end-to-end through payload
+# ==================================================================================================
+def test_real_ma_stack_entry_round_trips_end_to_end():
+    """The one PERMANENTLY closed hypothesis (registry status "closed"): its real ledger line must
+    appear in the real graveyard with byte-matching selectors/verdict AND its "closed" lineage."""
+    assert _CANONICAL_LEDGER.exists()
+    raw_entries = read_entries(str(_CANONICAL_LEDGER))
+    ma_stack_raw = next(e for e in raw_entries if e["claim"].get("factor") == "ma_stack")
+
+    payload = build_graveyard_payload()
+    ma_stack_rows = [
+        e for e in payload["entries"]
+        if e["ledger"] == LEDGER_CANONICAL and e["claim"].get("factor") == "ma_stack"
+    ]
+    assert len(ma_stack_rows) == 1
+    row = ma_stack_rows[0]
+    assert row["claim"] == ma_stack_raw["claim"]
+    assert row["verdict"] == ma_stack_raw["verdict"]
+    assert row["register_date"] == ma_stack_raw["register_date"]
+    assert row["verdict"]["status"] != "PASS"
+    assert row["lineage"] is not None
+    assert row["lineage"]["status"] == "closed"
+
+
+def test_real_graveyard_has_fourteen_entries_today_all_non_pass():
+    """Today BOTH real ledgers are 7/7 FAIL (goal.md's Evidence-frontier plateau note) -- every raw entry
+    is non-PASS, so the graveyard shows all 14. This is a STATUS-DERIVED assertion (computed from the raw
+    files), not a hardcoded expectation of the filter's behavior (a future PASS row would shrink this)."""
+    canonical_raw = [e for e in read_entries(str(_CANONICAL_LEDGER)) if e.get("type") != "forward_walk"]
+    staging_raw = [e for e in read_entries(str(_STAGING_LEDGER)) if e.get("type") != "forward_walk"]
+    expected_non_pass = sum(1 for e in canonical_raw + staging_raw if e["verdict"]["status"] != "PASS")
+
+    payload = build_graveyard_payload()
+    assert len(payload["entries"]) == expected_non_pass
+    assert all(e["verdict"]["status"] != "PASS" for e in payload["entries"])
+
+
+def test_real_graveyard_entries_carry_no_proven_language_in_verdict_status():
+    payload = build_graveyard_payload()
+    for entry in payload["entries"]:
+        assert entry["verdict"]["status"] in ("FAIL", "INSUFFICIENT")
diff --git a/apps/frontend/app/research/graveyard/page.tsx b/apps/frontend/app/research/graveyard/page.tsx
new file mode 100644
index 0000000..2a0b6dc
--- /dev/null
+++ b/apps/frontend/app/research/graveyard/page.tsx
@@ -0,0 +1,278 @@
+"use client";
+
+import { useEffect, useState } from "react";
+import Link from "next/link";
+import { AlertTriangle, Archive, ArrowLeft } from "lucide-react";
+
+import { useAsOfHref } from "@/components/asof-provider";
+import { PageHeading } from "@/components/page-heading";
+import { Badge } from "@/components/ui/badge";
+import { Card, CardContent } from "@/components/ui/card";
+import { fetchGraveyard, type GraveyardEntry, type GraveyardResponse, type RevisitProtocol } from "@/lib/api";
+import type { Verdict } from "@/lib/evidence";
+import type { PreRegistrationRow } from "@/lib/registry";
+import { formatIsoDate } from "@/lib/dates";
+import { cn } from "@/lib/utils";
+
+/**
+ * /research/graveyard — the negative-results graveyard (goal-mcp-loop iter-31, J-19 / backlog B-902).
+ *
+ * A read-only table of every hypothesis the referee has REJECTED (`FAIL` / `INSUFFICIENT`) across BOTH
+ * the canonical and staging certified-claims ledgers, joined to its registration lineage — so nobody (a
+ * future model, or the owner in month 9) re-derives a dead idea from scratch. Reads ONLY
+ * `GET /api/research/graveyard`; no forms, no mutations, no deletion path anywhere (append-only history).
+ *
+ * NO proven-language anywhere on this page: the Verdict column shows `FAIL`/`INSUFFICIENT` in the
+ * NEUTRAL-negative `danger`/`warn` Badge variants (mirrors the Evidence page's own PASS/FAIL/INSUFFICIENT
+ * mapping for these two statuses), NEVER the `accent` variant the Evidence page reserves exclusively for
+ * a PASS/"Proven" row — since this page shows only non-PASS rows, `accent` never appears here. The single
+ * source of "Proven" stays `/evidence`; this page never resolves or displays evidence status.
+ */
+export default function GraveyardPage() {
+  const [state, setState] = useState<State>({ kind: "loading" });
+
+  useEffect(() => {
+    const controller = new AbortController();
+    setState({ kind: "loading" });
+    fetchGraveyard(controller.signal)
+      .then((data) => setState({ kind: "ok", data }))
+      .catch(() => {
+        if (!controller.signal.aborted) setState({ kind: "error" });
+      });
+    return () => controller.abort();
+  }, []);
+
+  const entries = state.kind === "ok" ? state.data.entries : [];
+  const revisitProtocol = state.kind === "ok" ? state.data.revisit_protocol : null;
+
+  return (
+    <div className="space-y-4">
+      <div className="space-y-2">
+        <BackToResearch />
+        <PageHeading
+          title="Negative-results graveyard"
+          subtitle="Every hypothesis the statistical referee has rejected — out-of-sample FAIL or INSUFFICIENT, across both the canonical and internal staging ledgers — with its selectors, verdict, and registration lineage. Descriptive history only; nothing here is a proven/not-proven signal."
+        />
+      </div>
+
+      {state.kind === "loading" ? <GraveyardSkeleton /> : null}
+
+      {state.kind === "error" ? (
+        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
+          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
+          <div>
+            <p className="font-medium">Backend unavailable</p>
+            <p className="text-text-muted">
+              The graveyard could not load from the API. Confirm the backend is running and reload.
+            </p>
+          </div>
+        </Card>
+      ) : null}
+
+      {state.kind === "ok" && entries.length === 0 ? <GraveyardEmptyState /> : null}
+
+      {state.kind === "ok" && entries.length > 0 ? (
+        <>
+          <GraveyardTable entries={entries} />
+          {revisitProtocol ? <RevisitProtocolPanel protocol={revisitProtocol} /> : null}
+        </>
+      ) : null}
+    </div>
+  );
+}
+
+type State =
+  | { kind: "loading" }
+  | { kind: "ok"; data: GraveyardResponse }
+  | { kind: "error" };
+
+/** A same-window link back to the Research hub (mirrors `research/registry/page.tsx`'s pattern exactly). */
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
+/** The honest empty state — both ledgers absent/empty. Should not occur today (both real ledgers carry
+ *  7 non-PASS rows each), but the page must degrade gracefully rather than crash (anti-goal: resilience
+ *  to data-shape change). */
+function GraveyardEmptyState() {
+  return (
+    <Card data-testid="graveyard-empty">
+      <CardContent className="space-y-3 p-6">
+        <div className="flex items-center gap-2">
+          <Archive className="h-5 w-5 text-text-faint" aria-hidden />
+          <h2 className="text-sm font-semibold text-text">No rejected hypotheses yet</h2>
+        </div>
+        <p className="max-w-2xl text-sm text-text-muted">
+          Nothing has been referee-rejected yet on either ledger. Once a hypothesis fails, or is ruled
+          insufficient, out-of-sample, it appears here with its selectors, verdict, and registration
+          lineage.
+        </p>
+      </CardContent>
+    </Card>
+  );
+}
+
+function GraveyardTable({ entries }: { entries: GraveyardEntry[] }) {
+  return (
+    <Card className="p-0">
+      <div className="overflow-x-auto">
+        <table data-testid="graveyard-table" className="w-full border-collapse text-sm">
+          <thead>
+            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
+              <th className="px-4 py-2 font-medium">Selectors</th>
+              <th className="px-4 py-2 font-medium">Verdict</th>
+              <th className="px-4 py-2 font-medium">Date</th>
+              <th className="px-4 py-2 font-medium">Deflation</th>
+              <th className="px-4 py-2 font-medium">Ledger</th>
+              <th className="px-4 py-2 font-medium">Lineage</th>
+            </tr>
+          </thead>
+          <tbody>
+            {entries.map((entry, index) => (
+              <GraveyardRow key={`${entry.ledger}-${index}`} entry={entry} />
+            ))}
+          </tbody>
+        </table>
+      </div>
+    </Card>
+  );
+}
+
+/** The verdict-kind variant — NEUTRAL-negative only (`danger` for FAIL, `warn` for INSUFFICIENT), mirrors
+ *  the Evidence page's own `verdictVariant` mapping for these two statuses exactly. NEVER `accent`: this
+ *  page shows only non-PASS rows, so a "Proven"-style badge must never appear here. */
+function verdictKindVariant(status: string): "danger" | "warn" | "default" {
+  if (status === "FAIL") return "danger";
+  if (status === "INSUFFICIENT") return "warn";
+  return "default";
+}
+
+function GraveyardRow({ entry }: { entry: GraveyardEntry }) {
+  const isPermanent = entry.lineage?.status === "closed";
+  const verdict = entry.verdict ?? { status: "", reason: "" };
+  return (
+    <tr data-testid="graveyard-row" className="border-b border-border align-top last:border-b-0">
+      <td className="px-4 py-3">
+        <SelectorChips selectors={entry.claim} />
+      </td>
+      <td className="px-4 py-3">
+        <div className="flex flex-wrap items-center gap-1.5">
+          <Badge variant={verdictKindVariant(verdict.status)} data-testid="graveyard-verdict">
+            {verdict.status || "—"}
+          </Badge>
+          {isPermanent ? (
+            <Badge variant="default" className="text-text-faint" data-testid="graveyard-permanent">
+              permanent
+            </Badge>
+          ) : null}
+        </div>
+        {verdict.reason ? <p className="mt-1 max-w-xs text-xs text-text-faint">{verdict.reason}</p> : null}
+        <a
+          href="#revisit-protocol"
+          className="mt-1 inline-block text-[11px] text-text-faint hover:text-accent hover:underline focus-visible:text-accent focus-visible:outline-none"
+          data-testid="graveyard-row-revisit-link"
+        >
+          Revisit protocol →
+        </a>
+      </td>
+      <td className="num whitespace-nowrap px-4 py-3 text-text">{formatIsoDate(entry.register_date)}</td>
+      <td className="num whitespace-nowrap px-4 py-3 text-text-muted" data-testid="graveyard-deflation">
+        <DeflationLabel verdict={verdict} />
+      </td>
+      <td className="px-4 py-3">
+        <Badge variant="default" data-testid="graveyard-ledger">
+          {entry.ledger}
+        </Badge>
+      </td>
+      <td className="px-4 py-3">
+        <LineageLink lineage={entry.lineage} />
+      </td>
+    </tr>
+  );
+}
+
+/** `{deflation} ÷{deflation_divisor}` (e.g. `bonferroni ÷8`), or just the raw policy name when no divisor
+ *  is present (e.g. the staging online-FDR economy's `lord++`) — re-displays the referee's OWN recorded
+ *  deflation context verbatim, never recomputed. */
+function DeflationLabel({ verdict }: { verdict: Verdict }) {
+  const deflation = typeof verdict.deflation === "string" ? verdict.deflation : null;
+  if (!deflation) return <span className="text-text-faint">—</span>;
+  const divisor = verdict.deflation_divisor;
+  const hasDivisor = typeof divisor === "number";
+  return (
+    <span>
+      {deflation}
+      {hasDivisor ? ` ÷${divisor}` : ""}
+    </span>
+  );
+}
+
+/** A row's registration lineage: a link to its exact `/research/registry` row when matched, or an honest
+ *  "no lineage" text when the selector-set matches no registration (never a fabricated link). */
+function LineageLink({ lineage }: { lineage: PreRegistrationRow | null }) {
+  const asofHref = useAsOfHref();
+  if (!lineage) {
+    return (
+      <span className="text-xs text-text-faint" data-testid="graveyard-lineage-none">
+        No registration lineage
+      </span>
+    );
+  }
+  return (
+    <Link
+      href={asofHref(`/research/registry#registration-${lineage.id}`)}
+      className="text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
+      data-testid="graveyard-lineage-link"
+    >
+      {lineage.id} →
+    </Link>
+  );
+}
+
+/** Render a claim's selectors verbatim as compact key=value chips (mirrors the Registry page's
+ *  `SelectorChips` presentation) — read-only, re-formats nothing, no numeric edge. */
+function SelectorChips({ selectors }: { selectors: Record<string, unknown> }) {
+  const entries = Object.entries(selectors ?? {});
+  if (entries.length === 0) {
+    return <span className="text-text-muted">—</span>;
+  }
+  return (
+    <div className="flex max-w-xs flex-wrap gap-1">
+      {entries.map(([key, value]) => (
+        <Badge key={key} variant="default" className="num whitespace-nowrap text-[11px]">
+          {key}={Array.isArray(value) ? value.join("+") : String(value)}
+        </Badge>
+      ))}
+    </div>
+  );
+}
+
+/** The revisit-protocol panel — the single served rule every row's "Revisit protocol →" link anchors to. */
+function RevisitProtocolPanel({ protocol }: { protocol: RevisitProtocol }) {
+  return (
+    <Card id="revisit-protocol" className="scroll-mt-20" data-testid="graveyard-revisit-protocol">
+      <CardContent className="space-y-2 p-5">
+        <h2 className="text-sm font-semibold text-text">Revisit protocol</h2>
+        <p className="text-sm text-text-muted">{protocol.rule}</p>
+      </CardContent>
+    </Card>
+  );
+}
+
+function GraveyardSkeleton() {
+  return (
+    <Card className="space-y-2 p-4">
+      {Array.from({ length: 8 }).map((_, i) => (
+        <div key={i} className={cn("h-7 w-full animate-pulse rounded bg-surface-2")} />
+      ))}
+    </Card>
+  );
+}
diff --git a/apps/frontend/lib/graveyard.ts b/apps/frontend/lib/graveyard.ts
new file mode 100644
index 0000000..e136ac3
--- /dev/null
+++ b/apps/frontend/lib/graveyard.ts
@@ -0,0 +1,49 @@
+/**
+ * Negative-results graveyard types (goal-mcp-loop iter-31, J-19 / backlog B-902).
+ *
+ * Mirrors `lib/registry.ts`'s types-only pattern for the SEPARATE `GET /api/research/graveyard`
+ * payload — every NON-PASS referee verdict across BOTH the canonical and staging certified-claims
+ * ledgers, read VERBATIM (re-format only; nothing recomputed, nothing re-matched).
+ *
+ * This module carries NO proven-language and NO evidence-status resolution: `verdict.status` here is
+ * ALWAYS "FAIL" or "INSUFFICIENT" (the backend filters PASS out before this ever reaches the client) —
+ * a verdict-kind badge, never a "Proven"/"Not yet proven" signal. The ONLY source of "Proven" stays the
+ * certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file never touches that path.
+ */
+
+import type { Verdict } from "@/lib/evidence";
+import type { PreRegistrationRow } from "@/lib/registry";
+
+/** The two ledgers a graveyard entry may originate from — `"canonical"` (the user-facing, always-strict-
+ *  Bonferroni ledger) or `"staging"` (the internal exploration ledger, never served elsewhere). Surfacing
+ *  staging's NON-PASS rows here is the one deliberate, documented narrowing of the prior "staging is
+ *  internal-only" invariant; staging carries 0 PASS rows, so this never surfaces a proven-looking edge. */
+export type GraveyardLedger = "canonical" | "staging";
+
+/** One rejected (non-PASS) hypothesis, read VERBATIM from `GET /api/research/graveyard`. `claim` is the
+ *  EXACT cohort selector-set the referee tested (re-displayed as-is, same shape as a certified-claims row
+ *  or a registry row's `selectors`). `lineage` is the matched pre-registration row (`null` for an honest,
+ *  unregistered selector-set — no crash, no fabricated link). */
+export interface GraveyardEntry {
+  ledger: GraveyardLedger;
+  claim: Record<string, unknown>;
+  register_date: string | null;
+  horizon: number | null;
+  cohort_n: number | null;
+  control_n: number | null;
+  verdict: Verdict;
+  lineage: PreRegistrationRow | null;
+}
+
+/** The re-test policy (backlog B-406 / §0), served as a single constant so the page's panel and every
+ *  row's anchor agree on the SAME wording — descriptive governance text, never proven-language. */
+export interface RevisitProtocol {
+  rule: string;
+}
+
+/** The `GET /api/research/graveyard` payload: every non-PASS entry across both ledgers, plus the served
+ *  revisit-protocol constant. */
+export interface GraveyardResponse {
+  entries: GraveyardEntry[];
+  revisit_protocol: RevisitProtocol;
+}
```
