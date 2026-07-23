# Phase goal-ops-hardening-iter-13 — UI Test Results

**Phase:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL is driven mechanically by UT-07 (P1) failing — see "Read this first" below. The iteration's
     actual point (J-06 / the IndexSeriesCache hot-key latency fix) is DECISIVELY verified PASS with
     real numbers (max 219ms against a 1500ms budget, on a verifiably idle host, 3-for-3). UT-07 fails
     because the specific UI control it names does not exist on the live page — confirmed dead code,
     pre-dating this iteration by many iterations (0 frontend files changed this iteration). Read the
     UT-07 section before treating this FAIL as "the caching fix is broken." -->

**Overall:** 7/13 passed, 1 failed, 5 skipped (not exercised)

---

## Read this first — why the verdict is FAIL despite the core fix passing decisively

This report's top-line verdict is **FAIL** solely because **UT-07** (P1) fails, and the test plan's own
gate says: *"If any of UT-01, UT-02, UT-03, UT-04, UT-05, or UT-07 fails, the overall verdict must be
FAIL/PARTIAL regardless of how the other tests read."* I am following that gate literally and honestly,
per my instructions not to invent results — but the reason UT-07 fails is important context:

- UT-07 asks me to click a dropdown `aria-label="Range preset"` on the Dashboard's "Major indexes &
  regime" card and select "3M". **That control does not exist anywhere on the live page.** Live DOM
  query returned zero matches. Source-code grep confirms why: the component that owns this control,
  `apps/frontend/components/major-indexes-card.tsx`, is **not imported by any route file anywhere in
  `apps/frontend/`** (`grep -rn "MajorIndexesCard\|major-indexes-card" apps/frontend/app apps/frontend/components`
  returns zero hits outside the component's own defining file). It was replaced by the "Regime × phase
  cross-view" card in a much earlier iteration (documented in `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-*` and re-confirmed
  in `reports/phase-goal-mcp-loop-iter-22-ui-surface-map.md`, which explicitly instructs QA: *"do not
  spend time hunting for a second 'Major indexes & regime' card on any page"*). The live card
  (`phase-cross-view-card.tsx`) always calls `fetchIndexes(undefined, asof, ..., true)` — range is
  **always** `undefined`; there is no reachable UI path today that ever sends `range=3M` to the backend.
  This is a stale test-plan reference to dead code, **not a regression introduced by iter-13** (this
  iteration's diff touches zero `apps/frontend/` files, confirmed via `git status`/the surface map).
- The underlying *acceptance* UT-07 cares about — "the explicit non-default range request still uses
  the unchanged, uncached code path" — **is verified**, just not through this dead UI control: the dev
  handoff's own direct measurement (`GET /api/indexes?range=3M` via curl: 0.575s/0.582s, uncached) and
  my own fresh real-browser `fetch()` call from within a loaded Trendora tab (`fetch('.../api/indexes?range=3M')`
  → `200`, `661ms`, `10` series returned) both confirm the backend behavior is intact.
- Recommendation for the next iteration/test-plan pass: either retire UT-07 (the backend contract is
  already covered by `test_api_indexes.py`'s own TC-6) or rewrite it against the actual reachable
  control (the cross-view chart's client-side zoom/drag, which never calls a different `range` param at
  all — so a UI-level "non-hot-key path" check may not be expressible through today's UI at all).

**The five other P1 gate items (UT-01, UT-02, UT-03, UT-04, UT-05) all PASS**, and UT-03/UT-04 — the
canonical J-06 acceptance measurement, the actual point of this iteration — pass with a wide margin
(max 219ms observed against a 1500ms budget, i.e. ~7x headroom), not a marginal squeak.

---

## The canonical J-06 measurement (UT-03 / UT-04) — full numbers

**Technique:** real Chrome tabs via Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`),
each reading a genuinely fresh navigation (`new_tab` to the URL, then `close_tab` before the next
reading — never a reload of an existing tab). The backend's `GET /api/indexes?full=true` response
carries no `Cache-Control`/`ETag`/`Last-Modified` header (confirmed via `curl -sD -`), so Chrome's HTTP
cache never serves it from disk regardless of "disable cache" — cache is naturally, verifiably out of
the picture; DevTools Network-tab UI is not scriptable via this MCP tool, so I read the identical
underlying data (Resource Timing `duration`) via `performance.getEntriesByType('resource')`, which is
exactly the number DevTools' own "Time" column displays for the same request.

Each reading was cross-checked against `logs/hwmon/hwmon.csv` (nearest row at/after the reading's
wall-clock second) and `logs/backend.log` (no concurrent ingest job — `/api/data`'s `runs[0]` had a
populated `finished_at` and matched the pre-reading state throughout).

**Important, disclosed nuance:** on `/data`, two Resource Timing entries appear for
`GET /api/indexes?full=true` per load (e.g. `3.4ms` + `218.7ms`), not one. Root cause: the frontend
runs via `next dev` with `reactStrictMode: true` (confirmed in `next.config.js`), and
`IndexVendorPanel`'s mount effect has no `AbortController`/cleanup guard, so React 18 Strict Mode's
double-invoke-on-mount fires two real fetches. This is a **pre-existing dev-mode-only artifact**, not
caused by this iteration (the `/` page's `PhaseCrossViewCard` *does* have an abort-on-cleanup guard and
correctly avoids the double-fire — confirmed only one resource entry there). I report the **larger** of
the two per `/data` reading below as the conservative "Time" value.

| # | Page | Fresh nav method | `GET /api/indexes?full=true` duration | Wall-clock (UTC) | `hwmon` `load1` at/near that time | `mem_avail_mb` |
|---|------|------------------|----------------------------------------|-------------------|-----------------------------------|-----------------|
| 1 | `/data` | new tab → close | **218.7ms** (2 entries: 3.4ms + 218.7ms, StrictMode double-fire, see above) | 04:04:33 BST (03:04:33 UTC) | 0.69 | 16,246 MB |
| 2 | `/data` | new tab → close | **218.7ms** (3.4ms + 218.7ms) | 04:06:06 BST (03:06:06 UTC) | 0.36–0.41 | 17,419 MB |
| 3 | `/data` | new tab → close | **219.2ms** (3.5ms + 219.2ms) | 04:06:21 BST (03:06:21 UTC) | 0.50–0.54 | 17,321 MB |
| 4 | `/` (UT-04 spot-check) | new tab → close | **70.5ms** (single entry — no double-fire, abort guard present) | 04:06:48 BST (03:06:48 UTC) | 0.36–0.54 | 17,389–17,443 MB |

**All four readings ≤ 1500ms with wide margin (max 219.2ms, ~7x headroom). All four `load1` readings
< 2.0 (idle host, confirmed). All three `/data` readings' underlying vendor-panel table content was
byte-identical across the three loads** (10 rows, same vendor/first-bar values each time — confirmed via
`innerText` extraction, not just eyeballing).

The `index_series_cache` table's hot-key row survived the operator's clean restart (1 row, matching the
operator's own pre-check), so every one of these four readings served from the warm cache, exactly as
this iteration's `index_series_cached`/`index_series_cached_with_status` design intends.

---

## Technique note: `/data`'s ~17,800px page height and blank screenshots

Per the dispatch's own warning, this was reproduced exactly as described: a full-page **and** a
viewport-only screenshot taken after scrolling to the Run History table (deep in the DOM) both came
back **solid blank** (`UT-09-run-history.png`, `UT-09-run-history-viewport.png` — both single-color,
no content). This is a Chrome-MCP rendering limitation on this specific page's height/DOM depth, not a
product defect (the same page's *shallow* sections — the vendor panel, the job form — screenshot fine;
see `UT-02-result.png`, `UT-08-form-filled.png`).

**Technique used instead, for every deep-page assertion below:** `eval` → DOM query → `innerText`
extraction, executed at the same instant the assertion is being made (never relying on a screenshot to
"prove" deep-page state). E.g. `Array.from(document.querySelectorAll('table tr')).filter(tr =>
tr.innerText.includes('Refreshed'))` returned exact, verifiable text for all 41 visible run-history rows
in one call. This is documented here so a future QA pass on this same page doesn't waste time retrying
screenshots for deep sections.

---

## UT-08 / UT-09 / UT-10 — what I found trying to exercise the "index series" positive case

These three P2/P3 tests all depend on getting a live run whose `Refreshed:` line includes "index
series." I made a good-faith, bounded attempt (full detail below) and could not produce one live this
session — but the reason is informative, not a defect:

1. Ran one small, bounded `fetch` job (`2026-07-20 → 2026-07-22`, all symbols) — landed 1,764 new bars.
   Confirmed via `/api/data` coverage that all 10 configured `index_chart.symbols` (including SPY,
   QQQ, IWM, RSP, DIA) now carry bars through `2026-07-22` (previously capped at `2026-07-17`, the
   committed seed's ceiling) — so the index-series dataset-version stamp genuinely became stale.
2. However, **my own diagnostic `curl GET /api/indexes?full=true`** (checking `asof_date` right after
   the fetch) hit the route's own self-healing MISS path and silently re-warmed the cache **before** I
   submitted the follow-up backfill. `index_series_cached_with_status`'s HIT/MISS logic is identical
   whether triggered by a plain API read or by the ingest finalize hook — whichever gets there first
   "claims" the refresh. This is exactly the same self-healing behavior the dev handoff's own live
   verification independently observed (`docs/handoffs/goal-ops-hardening-iter-13-dev.md`, "Live
   Warm-Path Verification," item 1).
3. Ran the follow-up backfill (`2026-07-20 → 2026-07-20`) anyway to observe the ingest hook's own
   honesty gate: `aggregates_refreshed` = `["latest_snapshot","coverage","membership_timeline",
   "market_phase","research_hot_keys","drawdown_expectations"]` — **correctly, honestly omits**
   `"index_series"` (a cache HIT, nothing new to persist *this specific run* — the self-heal had
   already happened via my own read). No exception, no fabrication, confirmed via both the API and a
   live DOM read of the Run History table row for this run (`"Refreshed: latest snapshot, coverage,
   membership timeline, market phase, research hot keys, drawdown expectations"` — no "index series").
4. Tried once more: fetched `2026-07-23` (the fixture's true ceiling — 0 new bars landed, confirming
   `2026-07-22` is the actual boundary of fetchable offline fixture data). No further headroom to
   safely reproduce the positive case without additional ingest churn, which I judged disproportionate
   for two P2/P3 tests after already running 3 bounded jobs this session.
5. **Scanned all 41 visible `Refreshed:` rows in the live Run History table (DOM read, not just the
   API): zero contain "index series."** This is strong, if incomplete, honesty-gate evidence for UT-09's
   intent (the omission never fabricates), even without a positive comparison row.
6. **Disclosed, out-of-scope defect recurrence:** during step 3's backfill, the backend log shows the
   **known, pre-existing AG-8 `forward_testing.py:826` MemoryError** recurred ("ingest forward-aggregate
   warm aborted at horizon 1 — memory pressure"). Per the dispatch's explicit framing this is a known,
   out-of-scope defect — I am **not** treating it as a new finding. Unlike the prior turn's incident,
   this time it was **caught and isolated cleanly**: the job still completed `status: "ok"`,
   `GET /api/health` returned 200 throughout (confirmed via 3s-interval polling for the job's full
   ~4-minute duration), and the backend did not wedge. This is actually useful **positive** evidence for
   J-05's "stays responsive during heavy ingest" concern (J-05 itself is in the already-replay-verified
   set this run, so I am not filing a row for it — noting this only as a disclosed bonus observation).

**Disclosed side effect of this exploration:** fetching new SPY/QQQ/IWM/RSP/DIA/Stooq bars through
2026-07-22 without a matching backfill for every new date left the backend's `readiness` field reading
`"awaiting_snapshot"` (`readiness_detail`: *"New data has landed for the benchmark (SPY) through
2026-07-22, but no snapshot has been produced for that date yet. Run a backfill or rebuild on Data
Manager to produce it."*) at the end of this session, versus `"ready"` at the start. **This is not a
regression** — it is the exact honest, transitional status this ops-hardening goal is designed to show,
and I confirmed live that `/` and `/data` both continue to render correctly under it (no blank page, no
error overlay, chart and vendor panel both populated — see `UT-01-post-ingest-awaiting-snapshot.png`).
The operator may want to run one more backfill (`2026-07-21`/`2026-07-22`) to fully resolve it; I did not
do this myself to avoid further, unnecessary ingest churn after already running 3 jobs this session.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads without errors | smoke | P1 | Page renders, cards resolve to data, no console errors | Fresh nav to `/`: "Regime × phase cross-view" card (the live home of the historical "Major indexes & regime" content — see note) rendered with all 10 index lines + regime bands; no console errors; no skeleton stuck | PASS | `UT-01-result.png` |
| UT-02 | Data Manager loads without errors | smoke | P1 | `index-vendor-panel` + job-form card visible, resolves within seconds, no console errors | Fresh nav to `/data`: vendor panel populated (10 rows), job-form card visible, no `index-vendor-loading` skeleton stuck, no console errors | PASS | `UT-02-result.png` |
| UT-03 | Hot-key latency ≤1.5s, 3 fresh `/data` loads (canonical J-06 measurement) | happy-path | P1 | 3 fresh-nav `GET /api/indexes?full=true` readings ≤1500ms, host idle, content unchanged | Readings: 218.7ms / 218.7ms / 219.2ms — all ≤1500ms with ~7x margin; `load1` 0.36–0.69 all three times; vendor table byte-identical across all three loads | PASS | `UT-03-load1-result.png`, `UT-03-reading3.png` |
| UT-04 | Hot-key latency ≤1.5s, `/` spot-check | happy-path | P1 | 1 fresh-nav reading ≤1500ms, chart renders | Reading: 70.5ms (single entry, no StrictMode double-fire — abort guard present); `load1` 0.36–0.54; chart + tooltip both populated, as-of `2026-07-17` shown | PASS | `UT-04-result.png` |
| UT-05 | Vendor panel content unchanged | regression | P1 | Every configured symbol shows a named vendor or honest "—", no blanks | All 10 rows present (SPY/QQQ/IWM/RSP/DIA → "—"; ^SPX/^NDX/^DJI → Stooq; ^VIX → Yahoo; ^TNX → FRED-macro proxy), every first-bar date populated, no blank/undefined cell, no "Vendor disclosure unavailable" warning | PASS | `UT-02-result.png` (same panel read) |
| UT-06 | Dashboard chart content unchanged | regression | P2 | As-of date current, tooltip populated, both panes consistent | As-of `2026-07-17` shown (current trading day at test time); hover tooltip at `2025-08-15` showed all 10 index %, regime `Risk-on · 72/100`, phase `Expansion`, severity `26`, P(bear) `0.00` — fully populated, no "N/A" | PASS | `UT-06-tooltip-populated.png` |
| UT-07 | Non-default range preset still works | regression | P1 | `aria-label="Range preset"` dropdown selects "3M", chart re-renders shorter window | **Element does not exist on the live page** — `document.querySelectorAll('[aria-label="Range preset"]')` returned 0 matches; confirmed via source grep that the owning component (`major-indexes-card.tsx`) is dead code, unreachable from any route (0 imports outside its own file). See "Read this first" section for full analysis — not a regression from this iteration; underlying backend behavior independently confirmed via real-browser `fetch()` (200, 661ms, 10 series) | **FAIL** | none (element absent) |
| UT-08 | "index series" appears in Refreshed line | happy-path | P2 | New job's Refreshed line includes "index series" when gated | Could not reproduce live this session — my own diagnostic API read self-healed the cache before the ingest job's own turn (see "UT-08/09/10" section); positive path is unit-tested (`test_data_manager.py -k index_series`, 30 passed per dev handoff) but not exercised end-to-end via the live UI | SKIP (not exercised) | `UT-08-form-filled.png`, `UT-08-job-running.png` |
| UT-09 | "index series" honestly omitted elsewhere | regression | P2 | A row with it present + a row without it, both correct | Could not get a "present" row this session (see above); confirmed 0 of 41 visible Run History `Refreshed:` rows fabricate "index series" — the honest-omission gate held on every observed row, including a run whose date range genuinely landed new index-symbol bars | SKIP (partial evidence — omission confirmed broadly, positive-row comparison not possible) | DOM read (see report body); `UT-09-run-history.png`/`-viewport.png` are blank (see technique note) |
| UT-10 | Refreshed line reads clearly | ux | P3 | Plain-English list, "index series" styled identically to other items | No live instance of the string "index series" was available to inspect this session (see UT-08) | SKIP (not exercised) | none |
| UT-11 | Vendor-panel error state unchanged | error | P3 | "Vendor disclosure unavailable" wording on backend-down | No natural backend-down window occurred; I did not force one (services in this session are restarted only by the operator, per this iteration's pump note and explicit dispatch instruction) | SKIP (not exercised) | none |
| UT-12 | `/evidence` spot-check, no regression | regression | P2 | Within committed 3s budget, no console errors | `domContentLoaded` 581ms, `loadEvent` 761ms, `GET /api/evidence` 27ms — all well within the `≤3s` committed budget (`reports/perf-budgets.md`); no console errors | PASS | `UT-12-evidence-page.png` |
| UT-J-04 | Non-blocking boot with visible status (regression journey, dispatch-required) | regression | P1 | Restart→≤5s first-200, phase-aware badge, crash→honest-unreachable, log evidence, interrupted-job recovery | **Could not be exercised** — 5 of J-04's 6 steps require a live backend restart or kill, which I am explicitly instructed not to perform myself this run. See "J-04" section below for exactly what I could and could not confirm, and the exact operator action needed. | SKIP | none |

---

## Failed Tests

### UT-07 — Non-default range preset still works
**Verdict:** FAIL
**Failure:** The test step asks to click a dropdown with `aria-label="Range preset"` on the Dashboard.
This element does not exist anywhere on the live `/` page.

**Steps taken:**
1. Navigated to `http://localhost:3255/` (fresh, already-loaded and populated per UT-01/UT-04).
2. `document.querySelectorAll('[aria-label="Range preset"]')` → `[]` (zero matches).
3. Grepped the live frontend source for the aria-label and its owning component: found only in
   `apps/frontend/components/major-indexes-card.tsx:101`.
4. Grepped `apps/frontend/app/*.tsx` and `apps/frontend/components/*.tsx` for any import of
   `MajorIndexesCard` / `major-indexes-card` — zero hits outside the component's own file.
5. Read `apps/frontend/components/phase-cross-view-card.tsx` (the actual live card): its `fetchIndexes`
   call always passes `range=undefined` — there is no code path in the live app that ever sends a
   non-default `range` parameter to `/api/indexes` from the UI.
6. Corroborated the underlying backend acceptance anyway via a real-browser `fetch()` call from a live
   Trendora tab: `fetch('http://localhost:8255/api/indexes?range=3M', {cache:'no-store'})` → `200`,
   `661ms`, `10` series, `asof_date: "2026-07-20"`.

**Expected:** A dropdown labeled "Range preset" is clickable and selecting "3M" re-renders a shorter
window.
**Actual:** No such control exists on the page. This is confirmed dead code pre-dating this iteration
(surface maps from at least two much earlier iterations — `iter-22`, `iter-44` — already document this
component as orphaned/unreachable). Zero `apps/frontend/` files appear in this iteration's diff, so this
is not something iter-13 broke.
**Evidence:** none (absence of an element; see steps above for the exact commands run).

---

## Passed Tests

### UT-01 — Dashboard loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-01-result.png`
- Fresh navigation to `/`; the "Regime × phase cross-view" card (the current live home of the content
  historically called "Major indexes & regime" — the standalone card by that literal name was removed
  many iterations ago as a duplicate, per `apps/frontend/app/page.tsx`'s own code comment and multiple
  historical surface maps) rendered all 10 configured index lines, regime bands, and the phase/severity
  pane below it. No console errors (`get_console_messages` showed only the React DevTools info line).
  No skeleton stuck.

### UT-02 — Data Manager loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-02-result.png`
- Fresh navigation to `/data`; `[data-testid="index-vendor-panel"]` present and populated (10 rows),
  `[data-testid="index-vendor-loading"]` absent, "Start a fetch / backfill job" card visible, no console
  errors.

### UT-03 — Hot-key latency ≤1.5s, 3 fresh `/data` loads (canonical J-06 measurement)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-03-load1-result.png`,
`reports/qa/goal-ops-hardening-iter-13-evidence/UT-03-reading3.png`
- See the "canonical J-06 measurement" section above for full numbers. All three readings ≤219.2ms
  (≤1500ms budget), host idle throughout (`load1` 0.36–0.69), vendor-panel content byte-identical
  across all three loads.

### UT-04 — Hot-key latency ≤1.5s, `/` spot-check
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-04-result.png`
- 70.5ms reading (≤1500ms budget), `load1` 0.36–0.54, chart + tooltip both populated with real data.

### UT-05 — Vendor panel content unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-02-result.png`
- All 10 configured `index_chart.symbols` rows present; SPY/QQQ/IWM/RSP/DIA honestly show "—" (no
  vendor record); ^SPX/^NDX/^DJI show "Stooq"; ^VIX shows "Yahoo"; ^TNX shows "FRED-macro proxy". No
  blank/undefined vendor cell anywhere, no "Vendor disclosure unavailable" warning.

### UT-06 — Dashboard cross-view chart content unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-06-tooltip-populated.png`
- As-of date `2026-07-17` shown next to the card title (current trading day at test time, not stale).
  Hovered the chart's data area (near the right edge): tooltip populated for date `2025-08-15` with all
  10 index % values, regime label+score, phase, severity, P(bear), severity-velocity — no "N/A"/empty
  entries anywhere.

### UT-12 — `/evidence` spot-check, no regression
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-13-evidence/UT-12-evidence-page.png`
- `domContentLoadedEventEnd` 581ms, `loadEventEnd` 761ms — both well within the committed `≤3s` budget
  (`reports/perf-budgets.md`). `GET /api/evidence` resource-timing duration 27ms. No console errors.

---

## Skipped Tests

### UT-08 — "index series" appears in Refreshed line
**Verdict:** SKIPPED (not exercised)
**Reason:** Made a bounded, good-faith attempt (1 fetch job landing 1,764 new bars across all 10
configured index symbols, then 1 backfill job) but my own diagnostic API read self-healed the cache
before the ingest hook's own turn, so the positive flag was not observed live. See the "UT-08/09/10"
section above for the full mechanism and why this is not a defect. The positive code path is covered by
`apps/backend/tests/test_data_manager.py -k "index_series or finalize_hook"` (30 passed, per the dev
handoff) rather than a live end-to-end UI demonstration this session.
**Evidence:** `UT-08-form-filled.png`, `UT-08-job-running.png` (job mechanics confirmed working;
positive "index series" flag not captured).

### UT-09 — "index series" honestly omitted elsewhere
**Verdict:** SKIPPED (partial evidence gathered)
**Reason:** Depends on UT-08 producing a "present" row for comparison, which I could not reproduce (see
above). I did independently confirm, via a live DOM read of the Run History table, that **0 of 41**
visible `Refreshed:` rows fabricate "index series" — including the run whose date range genuinely
landed new index-symbol bars (run 134, correctly omitted because a prior read had already self-healed
the cache). This is meaningful honesty-gate evidence, just not the literal two-row comparison the test
specifies.
**Evidence:** DOM read quoted in the report body above; `UT-09-run-history.png` and
`UT-09-run-history-viewport.png` are both solid-blank (Chrome-MCP's known limitation on this page's
~17,800px depth — see the technique note above; not a product defect).

### UT-10 — Refreshed line reads clearly with the new item
**Verdict:** SKIPPED (not exercised)
**Reason:** Depends on a live instance of "index series" in the rendered text, which was not available
this session (see UT-08).
**Evidence:** none.

### UT-11 — Backend-error state on the vendor panel remains unchanged
**Verdict:** SKIPPED (not exercised)
**Reason:** No natural backend-down window occurred during this pass, and per this test's own
instruction and the dispatch's explicit constraint, I did not force a backend restart/kill solely to
exercise it. The backend was healthy (`GET /api/health` → 200) for the entire duration of this session.
**Evidence:** none.

### UT-J-04 — Non-blocking boot with visible status (regression journey)
**Verdict:** SKIPPED
**Reason:** J-04's 6 steps (per `docs/goal.md`'s "Must-have user journeys" section) are:
1. Restart backend via `scripts/start-backend.sh`; poll `GET /api/health` — **requires a live restart**.
2. Assert first-200 ≤5s — **requires the same restart**.
3. Restart again with frontend open; poll at ≤250ms; assert a pre-ready phase/progress payload and a
   matching badge state — **requires a live restart**.
4. Kill the backend (simulated crash); assert the UI shows an explicit unreachable/crashed state —
   **requires a live kill**.
5. Assert the persistent logfile contains boot events, and after the simulated crash ends abruptly (no
   clean-shutdown line) — **partially checkable without a fresh crash** (see below), but the "ends
   abruptly after a fresh crash" half needs step 4's live kill.
6. Restart; assert a job that was mid-flight at the kill now shows an explicit interrupted state —
   **requires the same live restart/kill sequence**.

Per my explicit instructions this run, I do not start/stop/kill services myself. What I *could* and did
confirm without any service action:
- The persistent backend logfile (`logs/backend.log`) exists, is append-only across restarts, and
  **does** contain boot events (`Started server process`/`Waiting for application startup`/`Application
  startup complete`/`Uvicorn running on http://0.0.0.0:8255`) for every restart in its history, including
  the operator's most recent clean restart onto pid `3013413` at line 31433 — confirming the logfile
  mechanism itself (J-04's "Consistency" acceptance bullet) is present and working, independent of any
  fresh crash I could trigger.
- The current, healthy backend's `GET /api/health` payload correctly carries a populated, structured
  `warmup: {done, total, status, message}` object and a `readiness` enum value (`"ready"` initially,
  later `"awaiting_snapshot"` — see the disclosed side-effect note above) — confirming the phase-aware
  health data contract J-04 depends on is present and well-formed, though I could not observe it
  transition through an actual "loading" phase without a live restart.
- I found **7 historical runs already marked `"interrupted"`** in the DB (ids 88, 94, 110, 113, 114,
  119, 124), from earlier crash/restart cycles in this multi-day goal-mode session — pre-existing
  evidence the interrupted-job-recovery mechanism (step 6) has worked before, though none of them is
  *fresh* from the specific incident this dispatch describes (all four backfill jobs from the
  golden-replay lane completed cleanly — `status: "ok"` — before the wedge occurred, so no job was
  actually orphaned by that specific incident).

**What is needed to complete J-04 this cycle:** an operator-initiated backend kill + restart cycle
(e.g. `SIGKILL` the current pid, then `scripts/start-backend.sh`), with a browser tab open polling `/`
and `GET /api/health` throughout, so a future continuation can capture steps 1-4 and 6 fresh. I am not
requesting this be done right now as part of this turn — flagging it here for the next continuation to
pick up, per the dispatch's framing that this is optional/best-effort within a single turn.
**Evidence:** none (no fresh crash cycle exercised).

---

## Golden replay scripts

No new golden scripts written this run. J-04 (the only regression journey this dispatch asked me to
execute fresh) could not be verified PASS — see above — so per the golden-script contract ("for every
journey you verify PASS") there is nothing to script for it. J-01/J-03/J-05's existing golden scripts in
`runs/goal-session-ops-hardening/journey-scripts/` are unchanged (already replay-verified this iteration
per the dispatch; I did not touch them). J-06's existing golden script (`journey-scripts/J-06.json`) is
also left unchanged — while UT-01–UT-04/UT-12 give strong fresh evidence for the two pages and one
spot-check this iteration actually touched, J-06's full acceptance spans 11 pages and I did not
individually re-verify the other 9 this session (per the test plan's own explicit scope note: this
iteration's effect is confined to `/` and `/data`'s shared endpoint plus one new word on `/data`, and the
plan directs regression checks only at those two pages plus one spot-check, not a full J-06 resweep).

---

## Environment

- **Frontend URL:** http://localhost:3255 (200 throughout this run; `next dev`, `reactStrictMode: true`
  — see the disclosed double-fetch nuance in the J-06 measurement section)
- **Backend URL:** http://localhost:8255 (pid `3013413`, restarted cleanly by the operator before this
  turn began; `GET /api/health` → 200 throughout this entire session, including through 3 bounded
  ingest jobs and one recurrence of the known AG-8 `forward_testing.py:826` MemoryError, which was
  caught and isolated cleanly this time — no wedge)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-23
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-13-evidence/`
- **Host safety:** `logs/hwmon/hwmon.csv` `load1` ranged 0.32–2.32 across this session (the one spike to
  2.32 was during the single-day backfill's forward-returns computation for 591 symbols, settling back
  to <1.0 within a couple minutes afterward); `mem_avail_mb` stayed 15,900–17,800 MB throughout — no AG-10
  hard-reset pattern, well clear of the 2-core-pinned host-guard ceiling. Three bounded ingest jobs were
  run this session (1 fetch 2026-07-20→22, 1 backfill 2026-07-20, 1 fetch 2026-07-23) — no
  heavy/full-universe/multi-year backfill, per the operator's constraint. No services were
  started/stopped/killed by this agent.
- **Disclosed residual state:** the backend's `readiness` now reads `"awaiting_snapshot"` (was `"ready"`
  at session start) as an honest side effect of the fetch jobs above landing new bars without a matching
  backfill for every new date — not a regression; both `/` and `/data` continue to render correctly
  under it. An optional follow-up backfill (`2026-07-21`/`2026-07-22`) would resolve it if desired.
