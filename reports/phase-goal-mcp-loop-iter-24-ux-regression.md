# Phase goal-mcp-loop-iter-24 — UX Regression Review

**Date:** 2026-07-09

**Verdict:** UX-REGRESSION-FAIL

<!-- FAIL: browser-qa-agent reproduced a P1 backend crash (MemoryError, then a fatal Rust/PyO3 panic) 2/2
     times on the very first `/data` load after a fresh restart (UT-16). This is the cold-boot condition
     every real deploy/restart cycle hits. It breaks: (a) this iteration's own target journey J-15's
     acceptance criterion ("cold /api/data completes ≤60s without OOM"), (b) the required-still-passing
     J-13 (Data Manager coverage + availability legend — cannot render when the request that serves it
     crashes the process), and (c) via the Rust-panic variant, which terminates the whole backend process,
     every OTHER page/journey in the product for the duration until an operator manually restarts it. A
     page that used to load now can, under the single most common real-world condition (a restart),
     crash the entire backend. That is not a discoverability gap — the new card and the pages around it
     are effectively inaccessible on cold boot, so FAIL rather than WARN. -->

## New Capability Discoverability

**Storage footprint card on `/data`** — the iteration's one new user-facing capability.

- **Navigation path:** confirmed at the code level (`apps/frontend/app/data/page.tsx:437-440`):
  `<CoveragePanel data={state.data} />` is immediately followed by
  `<StorageCapacityPanel capacity={state.data.capacity} />` in the page's render order — exactly matching
  the plan's "directly after CoveragePanel" requirement. From the Dashboard, "Data Manager" in the sidebar
  is a single click to `/data` (confirmed by browser-qa UT-13). No new page, no new nav entry needed —
  correct per the plan (this capability lives under the existing Data Manager home).
- **Within 2 clicks from home:** yes — 1 click (Dashboard → Data Manager), then the card is structurally
  the next section on the same page (no tab, no expand/collapse, no second navigation).
- **Label clarity:** "Storage footprint" with a "Database file" / "Price bars" / "Scanner rows" /
  "Forward returns" breakdown, each with a plain-language `definition` string rendered under the value
  (verified in source at `page.tsx:762-785`; verified rendered verbatim by browser-qa UT-14). Clear to a
  non-technical user — no jargon left unexplained.
- **Visual feedback:** read-only descriptive card; loads with the rest of the page's existing skeleton
  state, no separate loading spinner needed (matches the plan's stated design). Confirmed real numbers
  render and cross-check exactly against the `GET /api/data` `capacity` payload (browser-qa UT-02).
- **Minor observation (not a flag):** "Dataset coverage" embeds a 590-row per-symbol table with its own
  internal scrollbar directly before the new card begins, so reaching "Storage footprint" in practice
  takes roughly two screen-heights of scrolling past that table, not a single small wheel-tick as the
  test plan's "one click + one scroll" framing implied (browser-qa UT-13's own precision note). This does
  not rise to "undiscoverable" — there is no extra click, tab, or hidden interaction — but it is worth
  the product-manager's awareness if the Data Manager page keeps growing new cards below a
  progressively-taller coverage table.

**Assessment: discoverability itself is good.** The regression below is about the page's *reliability*,
not the new card's findability.

## Regression Risk

| Shared component / path | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `/data` cold-path request (`GET /api/data` → `data_manager.compute_coverage` / `_missing_data_diagnostic` / `compute_capacity`, `app/db.py`'s new pragma+pool config, `prices.py`'s `prefilled_bar_cache`) | **J-13** — Data Manager reflects the broadened universe; its coverage + per-date availability legend | Items B (WAL + `mmap_size_bytes=1GB` + `pool_size=10`/`max_overflow=20`), C (index drop/add), H (N+1 fix), K (new `compute_capacity` sharing the same request) all changed the exact request path this page's cold load exercises | **CRITICAL — confirmed, not potential.** browser-qa UT-16 reproduced a backend crash (`MemoryError` in `cursor.fetchmany()`/`json.dumps()`, then on a second clean attempt a fatal Rust/PyO3 panic that kills the process outright) on the very first `/data` load after every one of 2 independent fresh restarts. The coverage panel, the availability heatmap central to J-13, and the missing-data diagnostic panel never get a chance to render — the API call fails before responding. |
| Whole backend process (any page's API calls) | **J-01, J-03, J-04, J-05, J-10, J-12, J-14** (required-still-passing) and **J-15 itself** (this iteration's own target) | Same as above — but the second (Rust-panic) crash mode terminates the entire uvicorn process, not just the one request | **HIGH — cascading, conditional.** browser-qa's own scoping check (UT-16 step 7) confirmed `/api/stocks`, `/api/stocks/{ticker}`, and `/api/health` keep responding normally *as long as `/data` is never touched* — so the defect's *trigger* is narrowly `/data`'s cold path. But once the Rust-panic variant fires, the whole process dies, and every other page/journey goes dark (shows "Backend unavailable") until an operator manually restarts it. A user who simply clicks "Data Manager" after a deploy can take the entire product down for every other user in the meantime. |
| `/data` page's main-content fetch (`loadOverview` in `page.tsx`) vs. the global readiness badge (`useReadiness`/`HealthBadge`) | Page's own existing "Backend unavailable" error treatment (pre-dates this iteration) | Not edited this iteration, but its lack of auto-retry is what makes the crash's aftermath confusing | **MEDIUM — confirmed via code trace.** `loadOverview` (`page.tsx:260-297`) fires exactly once on mount (`useEffect` keyed on stable callbacks) with no polling and no retry-on-error; it only re-fires on an as-of change or a job completing. `HealthBadge` (`components/health-badge.tsx`) reads an independent `useReadiness` poll. Browser-qa UT-05 observed exactly the state this code implies: after the backend crashes and is restarted, the top-bar badge recovers to green "Ready" (it polls independently) while the `/data` page body stays stuck on the stale red "Backend unavailable" card — a visibly self-contradictory page (green badge, red card, same screen) that does not resolve without a manual reload. This is a pre-existing design gap (no retry affordance) newly *exposed* by this iteration's new crash condition — worth fixing alongside the crash itself since it is what turns a transient failure into a stuck, confusing dead end for a real user. |
| `snapshot_serving.stock_detail_payload` (item D, feeds `/stocks/{ticker}`) | J-02/J-10 (drill into a score's proof; deep price history + Full-history toggle) | Ticker-filtered fetch replaces whole-leaderboard deserialize | **LOW — verified, no regression.** browser-qa UT-08 confirmed `/stocks/AAPL` matches its leaderboard row exactly; UT-09 confirmed the Full-history toggle still works (1255 → 3185 bars, reverts cleanly). Both PASS. |
| `watchlist._canonical_rows` (item D) | J-12 (universe membership); watchlist workflow | Same ticker-filtered fetch, ticker-scoped | **LOW — verified, no regression.** browser-qa UT-10 confirmed an added MSFT row matches its `/stocks` row exactly. PASS. |
| `readiness.py` (item G) | Global readiness badge (every page) + `WarmingState` card (`/backtest`, `/research/*`) | Memoized SPY calendar + one grouped query replaces a per-date loop | **LOW — verified, no regression.** browser-qa UT-11 confirmed the badge shows correct states (Ready / red Backend-unavailable) on `/`, `/data`, `/stocks/AAPL`, and that `/api/health` meets its ≤0.1s budget (0.090-0.104s measured). `WarmingState`'s own conditional check (UT-12) could not be observed live (warm-up completed too fast on every restart in this session to catch the transient state) — skipped, not failed; low residual risk since the underlying value and query pattern were otherwise verified. |
| `models.py` index drop/add (item C) | `bars_asof` (scoring path), `max(date)`/availability queries | Removed 2 redundant indexes, added `ix_daily_prices_date` | **LOW — verified via `EXPLAIN QUERY PLAN`** per the dev handoff; no displayed value depends on index choice, only query cost. No UI-visible regression possible from this piece in isolation (its interaction with item B's pool/mmap sizing is exactly what produced the CRITICAL row above). |

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure | Status |
|---|---|---|
| `compute_capacity()` (item K) — DB file size + 3 row counts | `StorageCapacityPanel` on `/data`, 4 `DefinedMetric` values with plain-language definitions | **Full parity, verified.** browser-qa UT-02 cross-checked all 4 rendered values against the live `GET /api/data` `capacity` object — exact match, human-readable formatting, no raw byte count or unformatted integer leaked. |
| Items B/C/G/H (SQLite tuning, index hygiene, cheap readiness probe, N+1 fix) | No dedicated UI — correctly framed by `user-visible-changes.md` as "same output, faster," proof lives in `reports/perf-budgets.md` | **Correctly backend-only.** These are byte-identity-gated performance changes with no new capability to expose; not flagging as a gap — a "the app feels the same speed but is now measurably faster" outcome does not need its own UI element, and the phase's own DoD frames it this way. |
| `scripts/measure-perf.sh` + its `reports/perf-budgets.md` output (item K harness) | None — read from the repository, not the running app | **Correctly backend-only** (explicitly and honestly disclosed in `user-visible-changes.md`'s "Not Visible Yet" section as an intentional non-gap, not a deferred UI item). |
| **Claimed-vs-actual gap (parity of claims, not of surfaces):** `reports/perf-budgets.md`'s iter-24 section states the cold `/api/data` path "was re-verified this iteration: a fresh backend boot ... reached `readiness: ready` ... and answered `/api/health` with HTTP 200" as evidence that "items C/G/H's query-plan changes did not reintroduce the OOM or slow the cold path." | The dev's own committed evidence for the DoD's "cold `/api/data` path completes ≤60s without OOM" checkbox is actually a `/api/health` (readiness) measurement, not a `GET /api/data` measurement — a different code path. The report's own warm-latency table shows `GET /api/data` at 0.0149s, which is not a cold-boot number. | **Gap.** The claim in the committed budgets table does not match what browser-qa independently found when it exercised the *actual* `/data` page on a genuine fresh restart (UT-16: crash, 2/2). This is why the defect passed dev verification and reached browser QA before being caught — flagging so the perf-budgets.md claim is corrected alongside the underlying fix, not left standing as a false "re-verified" record. |

## Flags

### Hidden Capabilities
- None. The storage footprint card has a clear, direct navigation path (Dashboard → Data Manager → next
  card after Dataset coverage).

### Undiscoverable Capabilities
- None rising to this level. See the minor scroll-distance observation under Discoverability above —
  informational only, not blocking.

### Potential Regressions
*(Elevated from "potential" to "confirmed" for the first two — browser-qa already reproduced them with
hard evidence; listed here per the report template.)*

- **CONFIRMED — J-13 (Data Manager) broken on cold boot.** The `/data` page's coverage panel and
  per-date availability legend (J-13's core acceptance criteria) cannot render when the backend crashes
  serving `GET /api/data`'s cold-path computation, which browser-qa reproduced on 2/2 fresh restarts.
  Evidence: `reports/qa/goal-mcp-loop-iter-24-evidence/UT-16-backend-crash-log-excerpt.txt`, UT-06, UT-16
  in `reports/phase-goal-mcp-loop-iter-24-ui-test-results.md`.
- **CONFIRMED — cascading outage risk to every required-still-passing journey.** The Rust-panic crash
  variant terminates the whole backend process (not just the one request), which would present every
  other page (J-01, J-03, J-04, J-05, J-10, J-12, J-14) as "Backend unavailable" until an operator
  manually restarts it. The trigger is narrowly `/data`'s cold path (browser-qa confirmed other endpoints
  don't themselves crash), but the blast radius of the panic variant is the whole product.
- **CONFIRMED — readiness badge / page-content desync after the crash.** Traced in source: `/data`'s main
  content fetch (`loadOverview`, `page.tsx:260-297`) has no auto-retry and fires once on mount, while the
  top-bar `HealthBadge` polls independently via `useReadiness`. After a crash-and-restart cycle, a user can
  see a green "Ready" badge next to a stuck red "Backend unavailable" card on the same `/data` page,
  unresolved without a manual reload (browser-qa UT-05's recovery-continuation failure). Pre-existing
  design gap, newly exposed by this iteration's new crash condition.

### Visual Consistency
- **No inconsistency found.** Verified directly in source (`page.tsx:752-788`): `StorageCapacityPanel`
  reuses the exact `Card` / `PanelTitle` / `DefinedMetric` composition `CoveragePanel` uses, with the same
  `grid grid-cols-1 gap-3 p-4 sm:grid-cols-2` base pattern (a `lg:grid-cols-4` vs. `CoveragePanel`'s
  `lg:grid-cols-3` — a reasonable difference since the new card has 4 metrics vs. 6-7, not a token
  deviation). No arbitrary spacing/color values were introduced; no new card primitive was created. The
  repo has no separate `design-system.md` token file — consistency here is judged against the established
  component patterns other Data Manager panels already use, and the new panel matches them.
- The frontend diff for this iteration is purely additive (`git diff --stat`: `page.tsx` +61/-0,
  `lib/api.ts` +12/-0) — no existing component was edited, so no existing page's visual style could have
  been disturbed by this change.

## Recommendation

**Do not close this iteration on the current evidence.** This is a P1, reproduced (2/2), critical
anti-goal violation ("must never crash an existing page or exhaust a service's memory," `docs/goal.md`
anti-goal list) hitting both this iteration's own target journey (J-15's cold-path acceptance criterion)
and a required-still-passing journey (J-13), with a plausible full-outage blast radius via the Rust-panic
variant.

1. **Block on the UT-16/UT-06/UT-05 crash before re-running closure.** Root-cause it — browser-qa's own
   working hypothesis (not yet confirmed by an ablation) is that item B's new `mmap_size_bytes` (1 GB
   per-connection read-mmap window) combined with the new `pool_size=10`/`max_overflow=20` (up to 30
   pooled sqlite connections) may consume several GB of virtual address space before the existing
   ~3.27M-row bar prefill even starts, leaving too little headroom under the `server.memory_cap_mb: 6144`
   `ulimit -v` cap that iter-19 sized only against the Python-heap prefill cost. Worth verifying directly
   (toggle `mmap_size_bytes` off or shrink pool size, re-run the exact restart-then-`/data` repro) before
   shipping.
2. **Correct `reports/perf-budgets.md`'s iter-24 section** once fixed — its current "cold path re-verified"
   claim is backed by a `/api/health` measurement, not an actual `GET /api/data` cold-boot measurement;
   replace it with a genuine fresh-restart `/data` measurement so the committed budget table is trustworthy
   for future iterations that must re-assert it (per J-15's own acceptance step 3).
3. **Re-run the canonical browser-qa lane** (fresh restart → first `/data` load, at least twice) after the
   fix, specifically targeting this exact repro path, before considering J-13 or J-15 passing.
4. **Non-blocking, P3:** consider adding a retry affordance (or auto-retry) to `/data`'s error state so a
   transient backend failure doesn't strand the page in a stale, badge-contradicting state requiring a
   manual reload. Not required to unblock this iteration, but worth a follow-up card since it directly
   worsens the user-visible impact of any future backend hiccup on this page.

No action needed on the new card's own discoverability, labeling, or visual consistency — those are solid.
No action needed on items D/G's shared-component regression risk — both verified clean by browser-qa.
