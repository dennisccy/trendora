# Phase goal-i_can_see_the_wealthy_future_forever-iter-15 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: The frontend responds (HTTP 200) but serves a DEAD, UN-HYDRATED SSR shell on
     every route — its Next.js `next dev` server 404s on the framework client bundles, so React
     never hydrates, no data is fetched, and no interactive UI exists to test. This is an
     environment / build-state failure (a `next build` clobbered the running dev server's `.next`),
     NOT a defect in the iter-15 feature code. Reproduced in a clean, isolated browser (so it is not
     the concurrent-tab contention). The J-31 flow could not be exercised at any step. Per agent
     rules ("Do NOT mark FAIL merely because browser automation had trouble — note as SKIPPED with
     reason"), all 15 UI test cases are SKIPPED. -->

**Overall:** 0/15 tests passed — **15 SKIPPED** (0 PASS, 0 FAIL)

**Two independent blockers were found; either one alone forces SKIPPED:**

1. **PRIMARY — frontend serves a dead, un-hydrated shell on every route (build-state corruption).**
   In a *clean, isolated* headless browser (Playwright, no other tabs), both `/stocks` and `/research`
   load only their static SSR shell: the health badge is stuck on **"Checking backend…"**, every
   dropdown is stuck on **"Loading…"**, **0** table rows render, and **0** `/api/*` data requests are
   issued. Root cause: the running `next dev` server requests **unhashed** framework chunks
   (`/_next/static/chunks/main-app.js`, `/_next/static/chunks/app/layout.js`,
   `/_next/static/chunks/app-pages-internals.js`, `/_next/static/css/app/layout.css`) but on disk
   `.next/static/chunks/` holds only **content-hashed production-build** artifacts
   (`main-app-9475b33838c5bcd7.js`, `layout-d3ec390c7483b465.js`, `page-92d008…js`, `webpack-9ba9a59…js`).
   Every framework chunk therefore returns **HTTP 404** → React cannot hydrate → no client effect runs
   anywhere in the app. **This is independent of the iter-15 feature code** (the iter-15 diff is only
   `app/research/page.tsx` +35 and `app/stocks/page.tsx` +58/−4 — it does not touch framework chunks).

2. **SECONDARY — the Chrome MCP browser is shared by ≥3 concurrent QA runs.**
   The single shared headless Chrome (MCP daemon, port 9222) was simultaneously driven by this phase's
   `qa` agent (a Trendora tab it kept re-navigating to `/stocks?pattern=…`) **and** a different
   project's browser-QA ("Tapeology", `http://localhost:3650`, opening multiple tabs). Tabs and tab
   indices churned constantly; actors navigate by index and hijacked even a tab I opened myself
   (`set_profile` did not isolate — the MCP reuses one shared browser). This alone made MCP automation
   unreliable (the iter-6 "serialize browser access" hazard, here with an *uncoordinated third party*).
   It is secondary because blocker #1 reproduces even in a clean isolated browser with zero contention.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/research` loads with cross-link | smoke | P1 | Factor Lab + Setup&Pattern Lab render; cross-link visible | Dead SSR shell: "Checking backend…", Subject="Loading…", no cross-link, 0 fetches, 4× framework-chunk 404 | **SKIP** | `UT-01-research-dead-shell.png`; `TC-01-research-eventstudy-crosslink.png` (qa agent, same dead shell) |
| UT-02 | `/stocks` loads (Suspense OK) | smoke | P1 | Heading "Stocks", as-of badge, 3 filter dropdowns, ranked table | Dead SSR shell: only "View as-of date" select (Loading…), 0 rows, 0 fetches, 4× 404 | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-03 | Pattern cross-link → pre-filtered board | happy-path | P1 | `/research` cross-link → `/stocks?pattern=pullback_to_rising_dma__only`, 9 rows | Cross-link never renders (page un-hydrated); flow cannot start | **SKIP** | `UT-01-research-dead-shell.png` |
| UT-04 | Setup cross-link → pre-filtered board | happy-path | P1 | Cross-link → `/stocks?setup=Breakout-watch` | Cross-link never renders; flow cannot start | **SKIP** | `UT-01-research-dead-shell.png` |
| UT-05 | Deep-link pre-filter by pattern | happy-path | P1 | `/stocks?pattern=…__only` pre-applies Pattern filter, 9 rows | Dead shell on the deep-link too; Pattern dropdown never renders, 0 rows | **SKIP** | `UT-05-deeplink-dead-shell.png` |
| UT-06 | Deep-link pre-filter by sector | happy-path | P1 | `/stocks?sector=Energy` pre-applies Sector, 5 Energy rows | Dead shell; no dropdowns/rows hydrate | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-07 | Dropdown change reflects to URL (no scroll-jump) | happy-path | P1 | Selecting Pattern updates `?pattern=…`, no scroll jump | No interactive dropdowns exist (un-hydrated) | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-08 | Combined filters reflect to URL | happy-path | P2 | `?sector=…&setup=…` both reflected | No interactive dropdowns exist | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-09 | Cross-link renders for NA/low-sample subject | happy-path | P2 | Cross-link present for NA subject; caption asserts no count | Cross-link never renders (un-hydrated) | **SKIP** | `UT-01-research-dead-shell.png` |
| UT-10 | Unknown/empty pattern param → "all" | validation | P2 | `?pattern=garbage` → no crash, "All patterns", full list | Cannot evaluate fallback — filter UI never hydrates | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-11 | Zero-match deep-link → honest empty-state | error | P2 | Valid zero-match filter → "No stocks match these filters" | Cannot evaluate — table/empty-state never hydrates | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-12 | One date control; as-of keeps filter, no `as_of` param (PRINCIPAL RISK) | regression | P1 | As-of toggle re-points by date, filter intact, no `as_of` param | Cannot evaluate — no interactive date control or filters hydrate | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-13 | Travel ends on Stock Detail, scores consistent (DEFINING) | regression | P1 | Row click → `/stocks/[ticker]` with badge + 3 A–E scores + invalidation | Cannot reach — leaderboard never renders rows to click | **SKIP** | `UT-05-deeplink-dead-shell.png` |
| UT-14 | Existing dropdown filtering still works | regression | P1 | Setup dropdown narrows table; reset restores + clears URL | No interactive dropdowns exist (un-hydrated) | **SKIP** | `UT-02-stocks-dead-shell.png` |
| UT-15 | Cross-link discoverable & self-explaining | ux | P3 | Cross-link + caption visible under Subject selector | Cross-link never renders (un-hydrated) | **SKIP** | `UT-01-research-dead-shell.png` |

---

## Skipped Tests — shared root cause

All 15 cases share the **same** blocker. Rather than repeat it 15×, the single root cause and its
proof are documented here.

### Why the whole suite is SKIPPED (not FAIL)

The frontend **process is up** (`GET http://localhost:3835/` → 200, SSR HTML ≈ 41 KB) but it serves a
**non-functional shell**: the client JavaScript never loads, so React never hydrates and the app has no
interactive UI and fetches no data. The cause is a **`.next` build-cache corruption in the dev server**,
which is an **environment/build-state problem, not a defect in the iter-15 feature code**. Marking these
P1 cases FAIL would falsely report that the iter-15 J-31 work (the lab→leaderboard cross-link and the
URL-backed `/stocks` filters) regressed the app, which the evidence contradicts. The honest, accurate
verdict is therefore **SKIPPED — could not validate**, with the precise reason and fix below.

### Root-cause investigation (evidence chain)

1. **Backend is healthy and reachable (ruled out as the cause).**
   - `GET http://localhost:8835/api/health` → `200` in 0.028 s → `{"status":"ok","db_ok":true,"seed_latest_date":"2026-05-28",…}`
   - `GET http://localhost:8835/api/stocks` → `200`, 122 rows, asof `2026-05-28`.
   - `GET http://localhost:8835/api/research/event-study` → `200` in ~0.2 s, full subject catalog.
   - CORS correct for the browser origin: `access-control-allow-origin: http://localhost:3835`; preflight `OPTIONS` → 200.
   - The browser itself can reach the backend: an in-page `fetch('http://localhost:8835/api/health')` returned `{status:200, body:{status:"ok"…}}`.

2. **The frontend never hydrates — reproduced in a clean, isolated browser (rules out tab contention).**
   A standalone Playwright headless Chromium (no other tabs, no contention) loaded both routes and waited:
   | Route | health badge | table rows | `/api/*` requests | `_next/static` 404s |
   |-------|--------------|-----------:|------------------:|--------------------:|
   | `/stocks`   | "Checking backend…" (stuck) | 0 | 0 | 4 |
   | `/research` | "Checking backend…" (stuck) | 0 | 0 | 4 |
   No page-level JS exception was thrown; the only console output was 4× `Failed to load resource: 404`.

3. **The 404s are the framework client bundles** (identical on every route):
   ```
   404  /_next/static/css/app/layout.css?v=<changes-each-load>
   404  /_next/static/chunks/app-pages-internals.js
   404  /_next/static/chunks/main-app.js?v=<changes-each-load>
   404  /_next/static/chunks/app/layout.js
   ```
   Confirmed out-of-band: `curl http://localhost:3835/_next/static/chunks/main-app.js` → `404`
   (also `app-pages-internals.js` → 404, `app/layout.js` → 404).

4. **Why they 404 — `next dev` vs. a production `next build` clobbering the same `.next/`:**
   - The server is **`next dev`** (`package.json` `dev: "next dev"`; SSR HTML + `build-manifest.json`
     reference **unhashed** chunks: `rootMainFiles=["static/chunks/webpack.js","static/chunks/main-app.js"]`,
     plus `app/layout.js`, `app-pages-internals.js`, `polyfills.js`).
   - On disk, `.next/static/chunks/` holds **content-hashed production-build** artifacts instead:
     `main-app-9475b33838c5bcd7.js`, `webpack-9ba9a59ed9076ecb.js`, `layout-d3ec390c7483b465.js`,
     `page-92d008014835f8ff.js` — i.e. the output of a `next build`, **not** the unhashed files
     `next dev` serves.
   - `.next/diagnostics/build-diagnostics.json` = `{"buildStage":"static-generation",…}` — a fingerprint
     of a completed **production `next build`** (the iter-15 DoD step `cd apps/frontend && npm run build`),
     which overwrote the running dev server's `.next`. (Timestamps corroborate: hashed chunks + BUILD_ID at
     00:49; `webpack.js`/`app-build-manifest.json` rewritten 01:00–01:02 — straddling the QA window.)
   - Net effect: the already-running `next dev` process keeps emitting HTML that points at its expected
     unhashed dev chunks, but those files no longer exist on disk → 404 → **no hydration anywhere.**

5. **The iter-15 feature code is not implicated — and the production build itself succeeded.**
   `git diff --stat HEAD -- apps/frontend` = `research/page.tsx` (+35) and `stocks/page.tsx` (+58/−4)
   only — no change to layout, providers, `next.config`, or any framework bundle. The clobbering
   `next build` **completed successfully** (a full production `.next` exists: `BUILD_ID`
   `wOGVe68WvuBLXS_8p7g-5`, `prerender-manifest.json`, `routes-manifest.json`, and
   `diagnostics/build-diagnostics.json` at `buildStage:"static-generation"` — i.e. it got past
   compile/typecheck into static generation), so the iter-15 TypeScript **typechecks and builds clean**.
   A feature-code error would instead 404 a *page* chunk (`app/stocks/page.js`) and/or throw a hydration
   error overlay; here the **framework** chunks 404 with no overlay, which is a build-artifact mismatch
   from the dev/prod `.next` collision, not a source error.

6. **The phase's `qa` agent hit the identical wall.** Its pre-existing evidence shot
   `TC-01-research-eventstudy-crosslink.png` (captured 00:59) shows the **same dead shell** —
   "Checking backend…", Factor/Subject dropdowns "Loading…", and **no cross-link rendered** — i.e. it,
   too, could not get a hydrated render. Both QA agents were blocked by the same broken frontend.

### What this means for J-31

The defining J-31 browser flow (read Factor/Event-Study evidence → click the cross-link → land
pre-filtered on `/stocks` → open a row on `/stocks/[ticker]`) **could not be exercised at any step**,
because no interactive UI ever renders. **J-31 is therefore UNVERIFIED by browser QA this iteration**
(neither passed nor failed — blocked by the environment). The functional/API layer is independently
healthy (see §1), and a static review of the iter-15 diff is in the reviewer/coherence reports; but the
cross-page browser acceptance that J-31 specifically requires (iter-4 lesson: "defining-step evidence —
the full travel must actually be captured") was not obtainable in this environment.

### Remediation (so a re-run can actually validate J-31)

1. **Give the browser-QA dev server a clean, uncontaminated `.next`** and do **not** let `npm run build`
   write to the same directory the dev server serves from. Concretely, stop the `next dev` on :3835,
   `rm -rf apps/frontend/.next`, restart `next dev`, and run the production `npm run build` typecheck
   against a separate build dir (e.g. a distinct `distDir`/working copy) or *before* the dev server starts —
   never concurrently against the live dev `.next`.
2. **Re-run `browser-qa-phase.sh`** and confirm `GET /_next/static/chunks/main-app.js` → 200 and the
   health badge flips from "Checking backend…" to a ready state before executing UT-01…UT-15.
3. **Avoid sharing the MCP Chrome** with other concurrent browser-QA runs (this phase's `qa` agent and
   the unrelated "Tapeology" project on :3650). Serialize browser access or give each run its own browser
   so tab indices/navigation don't collide (iter-6 lesson).

After (1)–(3), the full 15-case plan — especially the P1 set UT-01/02/03/04/05/06/07/12/13/14 and the
J-18 principal-risk check (UT-12) — should be re-executed.

---

## Passed Tests

None — see SKIPPED root cause above.

## Failed Tests

None — no test reached an executable assertion (all blocked before any step could run). No P1/feature
failure is asserted, because the blocker is the dev server's build-state, not the iter-15 code.

---

## Environment

- **Frontend URL:** http://localhost:3835 — process up (HTTP 200) but **serving a non-functional,
  un-hydrated SSR shell** (framework chunks 404; React never hydrates).
- **Backend URL:** http://localhost:8835 — healthy (`/api/health` 200; `/api/stocks` 200, 122 rows,
  asof 2026-05-28; CORS correct for origin :3835).
- **Browser:** Chrome via MCP (shared, port 9222) — **unreliable**: concurrently driven by this phase's
  `qa` agent and a separate project's browser-QA ("Tapeology", :3650); tabs/indices churned, `set_profile`
  did not isolate. Definitive checks were therefore run in a **standalone isolated Playwright Chromium**,
  which confirmed the frontend (not the browser) is the primary blocker.
- **Test Date:** 2026-06-03
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-15-evidence/`
  - `UT-01-research-dead-shell.png` — `/research` dead shell (clean browser), 4× framework-chunk 404, "Checking backend…"
  - `UT-02-stocks-dead-shell.png` — `/stocks` dead shell (clean browser), only the as-of select, 0 rows, 4× 404
  - `UT-05-deeplink-dead-shell.png` — `/stocks?pattern=pullback_to_rising_dma__only` dead shell (deep-link also un-hydrated)
  - `TC-01-research-eventstudy-crosslink.png` — the `qa` agent's 00:59 capture, showing the **same** dead shell (cross-link never rendered)

### Ground-truth data captured for the eventual re-run (from the healthy backend API, asof 2026-05-28)

So the re-run can assert exact counts without re-deriving them:
- Pattern-flagged names: `pullback_to_rising_dma` = **9** (TPH, VRT, ETN, COST, GEV, ANET, ABNB, VKTX, ENTG);
  `flat_base_breakout` = **3** (TPH, GS, ADI); `vcp` = **4** (STX, TSLA, TSM, ORCL).
- Setups present: Avoid=102, Extended=11, Breakout-watch=8, Pullback-watch=1 (Actionable=0, Risk-off-watchlist=0 →
  UT-08/UT-14 should use **Extended** or **Breakout-watch**, not "Actionable" which has 0 rows today).
- Sectors: Energy = 5 (XOM, CCJ, UEC, DNN, LEU); Total = 122.
- **UT-11 zero-match note:** the test-plan's suggested `pattern=flat_base_breakout__only&setup=Avoid`
  actually matches **2** rows (GS, ADI), so it is **not** a zero-match. A genuine zero-match is
  `pattern=vcp__only&sector=Energy` (vcp names are all Tech/Cons-Disc; Energy has none) or
  `pattern=flat_base_breakout__only&sector=Energy`.
