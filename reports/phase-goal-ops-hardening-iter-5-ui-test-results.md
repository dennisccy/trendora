# goal-ops-hardening-iter-5 — UI Test Results

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** browser-qa-agent
**Scope of this pass:** TC-02 through TC-12 only (the 11 browser/page performance test cases from
`reports/qa/goal-ops-hardening-iter-5-test-plan.md`). TC-01 (backend cold-boot), TC-13 (code audit),
TC-15..TC-20 (artifact/regression/test-suite checks) are out of scope for this dispatch.

---

**Browser QA Verdict:** FAIL

**Overall:** 10/11 tests passed (1 failed on one sub-criterion of a six-part compound pass criteria)

The one failure (TC-02) is narrow and specific: the Dashboard's primary content, TTI, and 5 of its 6
named on-load endpoints all pass comfortably. Only `GET /api/indexes?full=true` — which feeds a
self-contained secondary chart panel with its own honest loading skeleton, not the main page gate —
misses its 1.5s sub-budget, reproducibly, in all 3 trials (1.68s / 2.19s / 2.05s). See TC-02 detail
below for full evidence and root-cause diagnosis. The iteration's headline fix (`/api/backtest`,
TC-10) is verified working correctly and reproducibly in real browser conditions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| TC-02 | Dashboard (`/`) TTI + on-load latencies | browser | P1 | TTI ≤3.0s; `/api/dashboard`,`/api/market-phase`,`/api/sectors`,`/api/themes`,`/api/indexes?full=true`,`/api/regime-history?full=true` each ≤1.5s | TTI (primary content) ~0.35–0.7s, full incl. secondary chart ~2.4–2.5s (both <3.0s); dashboard=7ms, market-phase=17–349ms, sectors=7–14ms, themes=6–9ms, regime-history=42–99ms (all PASS); **indexes=1678/2185/2054ms — FAILS 1.5s budget in 3/3 trials** | **FAIL** | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-02-dashboard.png` |
| TC-03 | Stocks (`/stocks`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/stocks` ≤1.5s | `/api/stocks`=182/123/126ms (3 trials, all PASS); page confirmed present in nav ("Stocks" link) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-03-stocks.png` |
| TC-04 | Stock detail (`/stocks/AAPL`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/stocks/AAPL` ≤0.3s | `/api/stocks/AAPL`=9ms (PASS, 33x under budget); reached via direct URL / ticker row, not top-nav | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-04-stock-detail-aapl.png` |
| TC-05 | Sectors (`/sectors`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/sectors` ≤1.5s | `/api/sectors`=14ms (PASS) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-05-sectors.png` |
| TC-06 | Themes (`/themes`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/themes` ≤1.5s | `/api/themes`=7ms (PASS) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-06-themes.png` |
| TC-07 | Data Manager (`/data`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/data` ≤1.5s warm / ≤2.0s cold | `/api/data`=59ms, 45ms (2 trials, PASS); page confirmed present in nav ("Data Manager" link); see notes for an out-of-scope-but-flagged finding on `/api/data/availability` | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-07-data-manager.png` |
| TC-08 | Evidence (`/evidence`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/evidence` ≤3.0s | `/api/evidence`=12ms (PASS); page confirmed present in nav ("Evidence" link) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-08-evidence.png` |
| TC-09 | Scanner Runs (`/scanner-runs`) TTI + latency | browser | P1 | TTI ≤3.0s; total on-load API latency ≤1.5s | `/api/runs`=142ms+148ms cumulative (PASS); 525 links rendered (~180+ runs); N+1 pattern confirmed not a problem at this scale | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-09-scanner-runs.png` |
| TC-10 | Backtest (`/backtest`) TTI + latency | browser | P1 | TTI ≤3.0s; `/api/backtest` within newly-committed budget (≤1.5–2.0s) | `/api/backtest`=118ms+275ms (trial 1), 115ms+254ms (trial 2) — **contingent `ForwardAggregateCache` fix confirmed working in real browser conditions, ~126–300x faster than the pre-fix 34,766ms** | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-10-backtest.png` |
| TC-11 | Watchlist (`/watchlist`) TTI + latency | browser | P2 | TTI ≤3.0s; `/api/watchlist` ≤1.5s | `/api/watchlist`=31ms (PASS); precondition confirmed — 6 real saved entries, xray/concentration analysis genuinely rendered (correlation matrix, clusters, sector/theme breakdown) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-11-watchlist.png` |
| TC-12 | Research Event-Study Lab (`/research/event-study`) TTI + latency | browser | P2 | TTI ≤3.0s; on-load API latency ≤1.5s | `/api/research/event-study?view=episodes`=46ms (PASS) | PASS | `reports/qa/goal-ops-hardening-iter-5-evidence/TC-12-research-event-study.png` |

**Correction to the dispatch's page-inventory notes:** all four pages the dispatch flagged as
"NOT in the nav list / verify if it exists" — Stocks, Stock detail, Data Manager, Evidence — ARE
present. The live nav bar (extracted directly from the running app) reads: Dashboard, Stocks, Themes,
Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager. All 11
target pages exist and were reached (10 via direct nav-bar link, 1 — stock detail — via a ticker
row/direct URL, which is standard for a detail page).

---

## Passed Tests

### TC-03 — Stocks (`/stocks`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-03-stocks.png`
- `GET /api/stocks` measured 182ms, 123ms, 126ms across 3 reloads — comfortably inside the 1.5s budget.
- **Flagged, non-reproducible anomaly (not scored as a failure):** on the first of 3 trials,
  `GET /api/evidence` (a layout-level call also present on this page) measured **42,857ms** in the
  browser's Resource Timing entry (`fetchStart`=831ms, `responseEnd`=43,688ms). This did NOT reproduce
  on 2 subsequent full page reloads (23ms, 28ms), nor across 3 direct `curl` calls to the same backend
  endpoint in isolation (12–24ms, byte-identical payload each time). Given the single occurrence, the
  otherwise-consistent fast readings everywhere else, and that this same QA session showed intermittent
  Chrome DevTools Protocol instability throughout testing (see Environment notes), this reads as a
  one-off measurement/tooling artifact rather than a real product defect — flagged here for the record,
  not counted against the verdict.

### TC-04 — Stock detail (`/stocks/AAPL`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-04-stock-detail-aapl.png`
- `GET /api/stocks/AAPL` = 9ms (budget ≤0.3s).
- Secondary on-load calls: `/api/stocks/AAPL/bars?through=latest`=643ms, `/api/regime-history`=108ms,
  `/api/evidence`=22ms — page fully settled by responseEnd≈1.78s, well inside the 3.0s TTI budget.

### TC-05 — Sectors (`/sectors`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-05-sectors.png`
- `GET /api/sectors` = 14ms (budget ≤1.5s), first-time browser measurement for this newly-committed
  budget.

### TC-06 — Themes (`/themes`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-06-themes.png`
- `GET /api/themes` = 7ms (budget ≤1.5s), first-time browser measurement.

### TC-07 — Data Manager (`/data`)
**Verdict:** PASS (against TC-07's literally-named criteria)
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-07-data-manager.png`
- `GET /api/data` = 59ms, 45ms across 2 reloads — comfortably inside both the 1.5s warm and 2.0s cold
  budgets.
- **Additional finding, outside TC-07's named scope, flagged for the record:** the page also fires
  `GET /api/data/availability` (feeds the coverage heatmap) at the same time as `/api/data`. This
  measured **2946ms and 3043ms** across 2 browser reloads — vs. 0.95–1.0s measured directly against the
  backend in isolation (3 curl trials) — the same "browser real-world load is ~3x isolated-backend load"
  pattern seen on TC-02's `/api/indexes?full=true` (see TC-02 root-cause diagnosis below). Verified by
  reading `apps/frontend/app/data/page.tsx` and `components/availability-heatmap.tsx`: this fetch is
  deliberately independent of the page's main loading gate (a separate `AvailabilityState`, "so the
  heatmap can show its own loading/error without blocking the rest of the page" per the code's own
  comment) and renders its own dedicated spinner (`data-testid="availability-loading"`,
  `Loader2 animate-spin`) while waiting — so the page's main content (confirmed fast, 45–59ms) is never
  blocked, and there is no blank/frozen frame. Not scored as a TC-07 failure since `/api/data/availability`
  is not one of TC-07's named pass-criteria endpoints, but the ~3x-over-any-reasonable-budget latency is
  real and reproducible (2/2) and may be worth a committed budget of its own in a future iteration.

### TC-08 — Evidence (`/evidence`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-08-evidence.png`
- `GET /api/evidence` = 12ms (budget ≤3.0s).

### TC-09 — Scanner Runs (`/scanner-runs`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-09-scanner-runs.png`
- `GET /api/runs` measured 142ms + 148ms (two calls — one layout-level prefetch, one page-owned fetch);
  cumulative on-load latency well inside the 1.5s budget. 525 links rendered (~180+ scanner runs),
  confirming the dev handoff's TC-13 conclusion that the per-run `ScannerResult` count N+1 pattern,
  while real, is not currently a performance problem at this table size.

### TC-10 — Backtest (`/backtest`) — highest-priority verification this iteration
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-10-backtest.png`
- Trial 1: `GET /api/backtest` = 118ms, 275ms (two calls). Trial 2 (fresh reload): 115ms, 254ms.
- This is the direct, independent browser-based confirmation of the iteration's contingent backend fix:
  the dev handoff and perf-budgets.md report the pre-fix violation at **34,766ms** and the post-fix
  curl-measured latency at **138ms**. My real-browser measurement (115–275ms across 2 independent page
  loads) confirms the fix holds under actual page-load conditions, not just isolated curl — roughly
  **126–300x faster** than the pre-fix state, comfortably inside the 1.5s budget both times.

### TC-11 — Watchlist (`/watchlist`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-11-watchlist.png`
- `GET /api/watchlist` = 31ms (budget ≤1.5s).
- Precondition explicitly verified, not assumed: extracted the rendered page text and confirmed 6 real
  saved entries (JNJ, KO, GOOGL, NVDA, MSFT, AAPL) with a fully-rendered `xray`/concentration section
  (pairwise correlation matrix, correlation clusters, sector concentration, theme concentration) — the
  `xray` payload field named in TC-11's steps was genuinely exercised, not a degenerate empty-list case.

### TC-12 — Research Event-Study Lab (`/research/event-study`)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-12-research-event-study.png`
- `GET /api/research/event-study?view=episodes` = 46ms (budget ≤1.5s).

---

## Failed Tests

### TC-02 — Dashboard (`/`) TTI and on-load API latencies
**Verdict:** FAIL (one of six named endpoint sub-criteria)
**Evidence:** `reports/qa/goal-ops-hardening-iter-5-evidence/TC-02-dashboard.png`

**What passed:** TTI for the Dashboard's primary content (nav, header, sector/theme panels — gated by
`{kind:"loading"} → <DashboardSkeleton/>` in `apps/frontend/app/page.tsx`) resolves in ~0.35–0.7s,
comfortably inside the 3.0s budget. Named endpoints: `/api/dashboard`=7ms (both trials),
`/api/market-phase`=349ms/17ms, `/api/sectors`=13ms/7ms, `/api/themes`=9ms/6ms,
`/api/regime-history?full=true`=42ms/99ms/91ms (3 trials) — all comfortably inside their 1.5s budgets.

**What failed:** `GET /api/indexes?full=true` measured **1678ms, 2185ms, 2054ms** across 3 independent
page loads — over its 1.5s budget in 3 of 3 trials (12–46% over budget each time). This is reproducible,
not noise.

**Root-cause diagnosis (measured, not speculative):**
- Direct backend `curl` to the same endpoint in isolation: 0.79–0.81s across 3 trials — inside budget.
- A simulated 10-request concurrent burst via `curl` (mimicking the Dashboard's actual on-load call set:
  health, dashboard, methodology, runs, market-phase, sectors, themes, indexes, regime-history,
  market-phase?full) run against the live backend measured `/api/indexes?full=true` at 0.89s — still
  inside budget, and every other endpoint stayed under 200ms.
- Yet all 3 real-browser trials showed 1.68–2.19s — roughly double the backend's own measured cost, in
  both isolated and simulated-concurrent conditions.
- The gap is most consistent with **browser-side connection queuing**: the Dashboard fires
  10–13 distinct requests to the same backend origin (`localhost:8255`) within the same ~10ms window on
  load. The backend serves plain HTTP/1.1 (uvicorn, no HTTP/2), and Chrome cross-origin connection reuse
  is capped at 6 concurrent connections per host — a `curl`-based simulation opens independent
  OS-level connections per request and does not reproduce this browser-specific cap, which likely
  explains why the burst-curl test stayed fast while the real browser did not.
- This is a genuine, real, user-facing finding, but it does **not** freeze or blank the page: verified
  by reading `apps/frontend/components/phase-cross-view-card.tsx` that this endpoint feeds
  `PhaseCrossViewCard`, a self-contained component with its own `status==="loading"` gate rendering an
  `animate-pulse` skeleton block — entirely independent of the main Dashboard's own loading gate. A real
  user sees the Dashboard's primary content (sectors, themes, header) within well under a second, with
  the cross-view chart panel showing an honest pulse-skeleton for roughly 2 more seconds before it
  populates. Total full-page settle time (main content + this secondary panel) is ~2.4–2.5s — still
  inside the page's own overall 3.0s TTI budget.

**Steps taken:**
1. Navigated to `http://localhost:3255/` 3 times (fresh reload each time), clearing/reading
   `performance.getEntriesByType('resource')` after each load.
2. Cross-checked `/api/indexes?full=true` directly against the backend via `curl` (isolated, then a
   10-request concurrent burst matching the page's real on-load call set).
3. Read the frontend source to confirm whether this endpoint's slow path blocks the page's interactivity
   or is isolated to an independently-loading secondary panel.

**Expected:** `/api/indexes?full=true` ≤ 1.5s on every trial.
**Actual:** 1678ms / 2185ms / 2054ms — over budget on 3 of 3 trials, by 12–46%.

---

## Skipped Tests

None. Chrome MCP was available and the frontend/backend were both reachable (HTTP 200) for the full
duration of this pass.

---

## Environment

- **Frontend URL:** http://localhost:3255 (prod-mode launcher per `scripts/start-frontend.sh`; note this
  script actually execs `npx next dev -p <port>` — this project's own standing "prod mode" convention is
  the persistent dev-server-on-a-fixed-port launched by the script, not a `next build && next start`
  production bundle. This is unchanged from every prior iteration's QA methodology, not a deviation
  introduced here — flagged only for accuracy.)
- **Backend URL:** http://localhost:8255 (`scripts/start-backend.sh`, confirmed HTTP 200 at
  `/api/health` throughout)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome DevTools
  Protocol). TTI and per-endpoint latencies were measured via the browser's own Navigation Timing and
  Resource Timing APIs (`performance.getEntriesByType('navigation'|'resource')`), read through `eval`,
  rather than visually reading the DevTools Network panel — this is the same underlying instrumentation
  DevTools' own Network tab reads from, and is more precise/reproducible for exact-millisecond duration
  capture than transcribing a rendered panel.
- **Test Date:** 2026-07-20
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-5-evidence/`
- **Console errors:** none observed across all 11 page loads (`get_console_messages` showed only
  Next.js Fast Refresh / React DevTools informational messages, consistent with dev-mode).
- **Tooling note:** this QA session's Chrome MCP connection showed intermittent
  `Page session timeout: Page.captureScreenshot` errors on roughly half of all `eval`/`screenshot`
  calls throughout the run (host load average was moderate — 0.25/0.40/0.61 on 16 cores — with several
  other unrelated `claude` processes active on the same machine). Every affected call was retried
  once and succeeded; no measurement in this report relies on a call that ultimately failed. This is
  flagged as context for the one non-reproducible anomaly noted under TC-03, and as a general caveat on
  this specific session's measurement environment (not a product-side finding).
