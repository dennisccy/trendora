# Goal-mcp-loop-iter-33 Functional Test Plan

**Phase:** goal-mcp-loop-iter-33 (J-20 — Daily Preflight Verdict)  
**Date:** 2026-07-14  
**Frontend Present:** yes

## Phase Goal

Deliver a single canonical daily preflight verdict (`GO` / `DEGRADED` / `NO-GO` + plain-language reasons) computed once in the backend and displayed as an unmissable banner on every decision surface (dashboard, `/stocks`, stock detail, `/watchlist`, `/evidence`, research), so users know at a glance whether today's board is safe to trust, with the concrete operational reasons if it is not.

---

## Test Cases

### TC-01 — Backend: `compute_preflight()` fixture matrix — GO state (all inputs healthy)

**Type:** api  
**Preconditions:**
- Backend service running at configured port (default http://localhost:8000)
- Seed data loaded with current data freshness (latest data date within configured threshold)
- Database reachable
- All ledger files (canonical, staging, registry) exist and are parseable

**Steps:**
1. Import `app.engine.readiness.compute_preflight` from the deployed backend code
2. Invoke with: `session=<db_session>`, `config=<ReadinessCfg>` where `freshness_max_age_days=30` (default), all component severity thresholds set to map healthy inputs → GO
3. Assert the returned object contains: `verdict="GO"`, `reasons=[]` (empty list for healthy state), `components={...}` with each input `ok=True`

**Expected outcome:** Function returns a dict with `verdict="GO"`, no reason strings (empty reasons list), all components healthy.  
**Pass criteria:** `returned["verdict"] == "GO"` AND `returned["reasons"] == []` AND all entries in `returned["components"]` have `ok=True`.

---

### TC-02 — Backend: `compute_preflight()` fixture matrix — DEGRADED state (freshness stale)

**Type:** api  
**Preconditions:**
- Backend service running
- Seed data loaded
- Database reachable
- Config `readiness.freshness_max_age_days = 5` (override to trigger stale)
- Data freshness: latest data date is > 5 trading days in the past (deterministic via seed/calendar, not wall-clock)

**Steps:**
1. Import `app.engine.readiness.compute_preflight`
2. Invoke with: `session=<db_session>`, `config=<ReadinessCfg>` where `freshness_max_age_days=5`, and the severity mapping for freshness is set to `severity="DEGRADED"`
3. Assert returned `verdict="DEGRADED"`
4. Assert `reasons` list includes a plain-language reason mentioning data staleness (e.g., "Data is N days old")
5. Assert `components.freshness.ok=False` and `components.freshness.severity="DEGRADED"`

**Expected outcome:** Verdict degrades to DEGRADED due to stale data; reason clearly states the data age.  
**Pass criteria:** `returned["verdict"] == "DEGRADED"` AND any(("old" in r.lower() or "stale" in r.lower()) for r in returned["reasons"]) AND `returned["components"]["freshness"]["ok"] == False`.

---

### TC-03 — Backend: `compute_preflight()` fixture matrix — NO-GO state (DB unreachable)

**Type:** api  
**Preconditions:**
- Config severity mapping: DB connectivity failure → `severity="NO-GO"`
- Mocked or real scenario where database connection fails (or DB temporarily unavailable)

**Steps:**
1. Simulate DB unreachability (either mock the session or temporarily stop the DB)
2. Invoke `compute_preflight(session=<broken_session>, config=<ReadinessCfg>)`
3. Assert returned `verdict="NO-GO"`
4. Assert `reasons` includes a plain-language reason mentioning DB connectivity (e.g., "Database unavailable")
5. Assert no exception is raised; the function returns a graceful NO-GO verdict

**Expected outcome:** Function gracefully returns NO-GO when DB is unreachable; reason explains the issue.  
**Pass criteria:** `returned["verdict"] == "NO-GO"` AND any(("database" in r.lower() or "db" in r.lower()) for r in returned["reasons"]) AND no exception is raised.

---

### TC-04 — Backend: `compute_preflight()` fixture matrix — NO-GO state (missing ledger file)

**Type:** api  
**Preconditions:**
- All ledger file paths resolve to valid locations (via existing path resolvers)
- Config severity mapping: ledger missing/unparseable → `severity="NO-GO"`
- Temporarily rename or delete one of the ledger files (canonical, staging, or registry)

**Steps:**
1. Rename one ledger file so it appears missing
2. Invoke `compute_preflight(session=<db_session>, config=<ReadinessCfg>)`
3. Assert returned `verdict="NO-GO"`
4. Assert `reasons` includes a plain-language reason mentioning the missing ledger
5. Restore the ledger file
6. Re-invoke `compute_preflight()` and assert `verdict` is healthy again

**Expected outcome:** Missing ledger triggers NO-GO; restoring it returns to healthy state.  
**Pass criteria:** First call: `returned["verdict"] == "NO-GO"` AND "ledger" in reasons. Second call (after restore): verdict is GO or DEGRADED (depending on other inputs).

---

### TC-05 — Backend: `compute_preflight()` — severity mapping config wiring (DEGRADED vs NO-GO is configurable)

**Type:** api  
**Preconditions:**
- Same trigger condition (e.g., stale freshness) can be mapped to either DEGRADED or NO-GO depending on config
- Two config instances: one with `{freshness: DEGRADED}`, one with `{freshness: NO-GO}`

**Steps:**
1. Invoke `compute_preflight()` with config mapping freshness → DEGRADED
2. Assert `verdict="DEGRADED"`
3. Invoke `compute_preflight()` with identical state but config mapping freshness → NO-GO
4. Assert `verdict="NO-GO"`

**Expected outcome:** Same input state yields different verdicts based on config severity mapping, not hardcoded logic.  
**Pass criteria:** Same condition produces `verdict="DEGRADED"` with first config, `verdict="NO-GO"` with second config.

---

### TC-06 — Backend: `compute_readiness()` output byte-identity (J-40 regression guard)

**Type:** api  
**Preconditions:**
- Existing `compute_readiness()` function is called both before and after iter-33 deployment
- Identical session/warmup state for both calls

**Steps:**
1. Call `compute_readiness(session=<db_session>)` on a known as-of date
2. Record the returned `state` and `warmup` fields as bytes
3. After `compute_preflight()` is integrated into the health endpoint, call `compute_readiness()` again with the same session
4. Compare the byte representations of `state` and `warmup` — they must be identical

**Expected outcome:** `compute_readiness` output is byte-identical; no regression in existing readiness badge logic.  
**Pass criteria:** MD5(output_before) == MD5(output_after) for the `state` and `warmup` fields.

---

### TC-07 — Backend: `GET /api/health` additive-shape test (preflight field present, existing keys unchanged)

**Type:** api  
**Preconditions:**
- Backend running
- Health endpoint reachable at `GET /api/health`

**Steps:**
1. Invoke: `curl -s http://localhost:8000/api/health | jq .`
2. Assert response contains all existing keys: `state`, `warmup`, `timestamp`, etc. (capture from a known-good snapshot)
3. Assert response now contains a NEW key: `preflight`
4. Assert `preflight` has expected shape: `{verdict: string, reasons: array, components: object, as_of: string|null, reference: string|null}`
5. Assert the `state` and `warmup` values are identical to a pre-iter-33 snapshot

**Expected outcome:** Health payload is additive; old keys unchanged, new `preflight` key present with correct structure.  
**Pass criteria:** Response has all old keys, new `preflight` key is present and parses as valid JSON with the expected fields.

---

### TC-08 — Backend: Verdict history append-on-transition (not on every poll)

**Type:** api  
**Preconditions:**
- Verdict history file exists at config-resolved path (default or overridden via env)
- File is initially empty or in a known state

**Steps:**
1. Call `GET /api/health` twice with 2-second delay, capturing the `preflight` verdict both times (healthy state)
2. Read the verdict history file; record its byte count
3. Call `GET /api/health` again, expecting same verdict (GO)
4. Read the verdict history file again; assert byte count is unchanged (no append)
5. Change config to force a stale state (lower `readiness.freshness_max_age_days`)
6. Call `GET /api/health`; observe verdict changes to DEGRADED
7. Read the verdict history file; assert it now contains an entry for the transition
8. Call `GET /api/health` again (still DEGRADED)
9. Read the verdict history file; assert no additional entry was appended (same byte count as step 7)

**Expected outcome:** History log grows only on verdict transitions, not on every poll.  
**Pass criteria:** File size unchanged after repeated same-verdict polls; file grows exactly once when verdict changes, no further growth on subsequent same-verdict polls.

---

### TC-09 — Backend: Single-source verification (no duplicate compute path)

**Type:** artifact  
**Preconditions:**
- Source code deployed and accessible

**Steps:**
1. Search codebase for all calls to `compute_preflight`: grep -r "compute_preflight" apps/backend/
2. Assert exactly one producer: the call site should be only in `apps/backend/app/api/health.py`
3. Search codebase for all assignments to fields named `preflight` or similar: grep -r "preflight.*=" apps/backend/
4. Assert no per-page or per-route logic computes or caches a separate readiness verdict (should be on the health path only)

**Expected outcome:** Single canonical producer of the `preflight` field, served only via `/api/health`.  
**Pass criteria:** Exactly one call to `compute_preflight()` exists in the codebase, in the health endpoint only.

---

### TC-10 — Frontend: PreflightBanner component exists and mounts once in app shell

**Type:** browser  
**Preconditions:**
- Frontend running at configured URL (default http://localhost:3000)
- Backend service running and healthy (GO state)

**Steps:**
1. Open Chrome browser; navigate to http://localhost:3000/
2. Inspect the DOM using Chrome DevTools (F12)
3. Search for the `PreflightBanner` component or its rendered banner element (CSS class or data attribute)
4. Assert the component is rendered exactly once in `<main>` or the layout root (not repeated per page)
5. Navigate to `/stocks` and inspect the DOM; assert the banner is still present and unchanged
6. Navigate to `/watchlist` and repeat; banner should be present everywhere

**Expected outcome:** Banner is mounted once in the layout, visible on all routes.  
**Pass criteria:** DOM inspection finds the banner element in `app/layout.tsx` wrapper (parent of route outlets), appearing once per page load regardless of route.

---

### TC-11 — Frontend: GO state banner renders quiet, non-intrusive strip (healthy state)

**Type:** browser  
**Preconditions:**
- Frontend running, backend healthy (GO verdict)
- Latest data within configured freshness threshold
- Database and ledger files all present

**Steps:**
1. Navigate to http://localhost:3000/ (dashboard)
2. Take a full-page screenshot (`TC-11-dashboard-go.png`)
3. Inspect the banner element: assert it is visible but does not disrupt page layout
4. Assert the banner uses CSS token `--pos` (success/green color)
5. Assert the banner text reads "GO" or similar quiet affirmation (no reasons list)
6. Navigate to `/stocks` and take a screenshot (`TC-11-stocks-go.png`)
7. Visually confirm the banner text/color is identical to the dashboard banner

**Expected outcome:** GO banner is quiet, consistent, pixel-visible on both dashboard and stocks page.  
**Pass criteria:** Banner is rendered with `--pos` token, text reads "GO", and screenshots on dashboard and `/stocks` show identical banner content/color (md5-distinct from DEGRADED/NO-GO frames).

---

### TC-12 — Frontend: DEGRADED state banner renders loud with reasons (stale freshness)

**Type:** browser  
**Preconditions:**
- Frontend running
- Config override to force stale data (lower `readiness.freshness_max_age_days` or pin reference forward)
- Backend restarted with new config

**Steps:**
1. Stop backend service
2. Override config: `readiness.freshness_max_age_days = 0` (force immediate stale state)
3. Restart backend
4. Refresh frontend at http://localhost:3000/
5. Inspect the banner: assert it now uses CSS token `--warn` (amber/caution color)
6. Assert the banner text reads "DEGRADED" and lists reasons (e.g., "Data is X days old")
7. Take a full-page screenshot (`TC-12-degraded.png`)
8. Restore config to original value and restart backend
9. Refresh frontend; assert banner returns to GO state

**Expected outcome:** DEGRADED banner is loud, amber, lists concrete reasons, and dismisses when condition clears.  
**Pass criteria:** Banner CSS class/color is `--warn`, text includes "DEGRADED" and at least one reason phrase, screenshots are md5-distinct from GO frame.

---

### TC-13 — Frontend: NO-GO state banner renders loud with critical reason and exact text

**Type:** browser  
**Preconditions:**
- Frontend and backend running
- Config set to map DB unavailability to NO-GO
- Capability to temporarily disconnect or block database

**Steps:**
1. Identify the database connection string in config
2. Modify backend config to point to a non-existent or unreachable DB server (e.g., `localhost:9999`)
3. Restart backend
4. Refresh frontend at http://localhost:3000/
5. Inspect the banner: assert it uses CSS token `--neg` (danger/red color)
6. Assert the banner text reads "NO-GO" and lists reasons (e.g., "Database unavailable")
7. Assert the banner contains the EXACT phrase: "do not rely on today's board"
8. Take a full-page screenshot (`TC-13-nogo.png`)
9. Restore database config and restart backend
10. Refresh frontend; assert banner returns to GO state

**Expected outcome:** NO-GO banner is loud, red, contains the exact required phrase, and clears when DB recovers.  
**Pass criteria:** Banner CSS class/color is `--neg`, text includes "NO-GO" and "do not rely on today's board", screenshot is md5-distinct from GO and DEGRADED frames.

---

### TC-14 — Frontend: Banner is single-source (no per-page recompute via DOM inspection)

**Type:** browser  
**Preconditions:**
- Frontend running, backend healthy

**Steps:**
1. Open Chrome DevTools Network tab; filter for API calls
2. Navigate to http://localhost:3000/ (dashboard)
3. Record all API calls; assert one call to `GET /api/health` (the ReadinessProvider poll)
4. Inspect the banner in DevTools; confirm it reads `preflight` from the context (use React DevTools to inspect `useReadiness()` hook)
5. Navigate to `/stocks` and repeat; assert still only ONE `/api/health` call per page (the provider's ~2s poll), not a per-page fetch
6. Assert no local `compute_*` or `useState()` logic in any page component that would re-derive the verdict

**Expected outcome:** Banner reads only the provider context; no per-page API calls or computation.  
**Pass criteria:** Network tab shows single `/api/health` poll per page, React DevTools confirms banner reads from `useReadiness()` context, no page-local logic.

---

### TC-15 — Frontend: ReadinessProvider extended to expose preflight (type in lib/api.ts)

**Type:** artifact  
**Preconditions:**
- Source code accessible

**Steps:**
1. Read `apps/frontend/lib/api.ts`; verify `HealthStatus` type includes `preflight?: {...}` field
2. Read `apps/frontend/components/readiness-provider.tsx`; verify the context value type includes `preflight` field
3. Assert the `tick()` function (or equivalent polling) calls `fetchHealth()` once (no additional fetches for preflight)
4. Verify `useReadiness()` hook returns the context with `preflight` exposed

**Expected outcome:** Types are correctly wired; preflight is optional (loading state) and comes from the same `/api/health` call.  
**Pass criteria:** `HealthStatus` type has `preflight?: Preflight` field; `ReadinessContextValue` includes `preflight`; only one `fetchHealth()` call in provider.

---

### TC-16 — Browser: J-20 dashboard page renders GO banner without disrupting layout

**Type:** browser  
**Preconditions:**
- Frontend and backend running, both healthy
- Dashboard has a known visual baseline (from prior iterations or a screenshot file)

**Steps:**
1. Navigate to http://localhost:3000/
2. Compare the full-page screenshot to a known-good dashboard baseline
3. Assert the banner is visible (new element above `<main>`)
4. Assert the page layout is not disrupted (no elements pushed down or hidden by the banner)
5. Assert key dashboard components (e.g., leaderboard table, regime badge) are still visible and at expected positions

**Expected outcome:** GO banner adds a thin strip at the top; existing page layout is preserved.  
**Pass criteria:** Banner is present, layout unchanged, key page elements still visible in expected positions.

---

### TC-17 — Browser: J-20 `/stocks` page renders GO banner without disrupting leaderboard

**Type:** browser  
**Preconditions:**
- Frontend and backend running, both healthy

**Steps:**
1. Navigate to http://localhost:3000/stocks
2. Take a full-page screenshot (`TC-17-stocks-go.png`)
3. Inspect the leaderboard table; assert all rows are visible
4. Assert the GO banner is visible above the leaderboard
5. Inspect at least 3 leaderboard rows; assert data (ticker, scores, evidence badges) are fully visible

**Expected outcome:** GO banner is present on stocks page; leaderboard is not disrupted.  
**Pass criteria:** Banner visible, leaderboard rows fully visible with all data columns present.

---

### TC-18 — Browser: J-20 stock detail page (e.g., `/stocks/NVDA`) renders GO banner

**Type:** browser  
**Preconditions:**
- Frontend and backend running, both healthy

**Steps:**
1. Navigate to http://localhost:3000/stocks/NVDA
2. Take a full-page screenshot (`TC-18-stock-detail-go.png`)
3. Assert the GO banner is visible
4. Assert the stock detail page (charts, metrics, scores) is fully rendered

**Expected outcome:** GO banner appears on stock detail routes.  
**Pass criteria:** Banner visible; stock detail page fully rendered.

---

### TC-19 — Browser: J-20 `/watchlist` page renders GO banner

**Type:** browser  
**Preconditions:**
- Frontend and backend running, both healthy

**Steps:**
1. Navigate to http://localhost:3000/watchlist
2. Take a full-page screenshot (`TC-19-watchlist-go.png`)
3. Assert the GO banner is visible
4. Assert any watchlist content is fully visible below the banner

**Expected outcome:** GO banner appears on watchlist page.  
**Pass criteria:** Banner visible; watchlist content fully rendered.

---

### TC-20 — Browser: J-20 `/evidence` page renders GO banner

**Type:** browser  
**Preconditions:**
- Frontend and backend running, both healthy

**Steps:**
1. Navigate to http://localhost:3000/evidence
2. Take a full-page screenshot (`TC-20-evidence-go.png`)
3. Assert the GO banner is visible
4. Assert the evidence ledger table is fully visible

**Expected outcome:** GO banner appears on evidence page.  
**Pass criteria:** Banner visible; evidence ledger rendered.

---

### TC-21 — Browser: All surfaces show identical GO banner text (consistency across routes)

**Type:** browser  
**Preconditions:**
- All five surfaces reachable and healthy (dashboard, `/stocks`, `/stocks/{ticker}`, `/watchlist`, `/evidence`)

**Steps:**
1. Visit each of the 5 surfaces (TC-16 through TC-20)
2. Extract the banner's text/color from each screenshot or DOM inspection
3. Assert the banner renders identically (same text, same CSS tokens) on all 5 surfaces

**Expected outcome:** Single banner design rendered consistently everywhere.  
**Pass criteria:** Banner text and visual treatment (color, size, spacing) are identical across all 5 surfaces.

---

### TC-22 — Browser: Induced DEGRADED state shows on all surfaces with reasons

**Type:** browser  
**Preconditions:**
- Frontend running
- Backend restarted with stale-freshness config override

**Steps:**
1. Override `readiness.freshness_max_age_days = 0` and restart backend
2. Visit each of the 5 surfaces (dashboard, `/stocks`, `/stocks/{ticker}`, `/watchlist`, `/evidence`)
3. Take a screenshot of each (`TC-22-dashboard-degraded.png`, etc.)
4. Assert each screenshot shows a DEGRADED banner (amber color, `--warn` token) with reasons listed
5. Assert all 5 screenshots show identical reasons list

**Expected outcome:** Induced stale state surfaces on all pages with consistent reasons.  
**Pass criteria:** All 5 surfaces show DEGRADED banner with identical reasons; screenshots are md5-distinct from GO frames.

---

### TC-23 — Browser: Induced NO-GO state shows on all surfaces with "do not rely" text

**Type:** browser  
**Preconditions:**
- Frontend running
- Backend restarted with DB unreachable config (or DB stopped)

**Steps:**
1. Stop the database or point backend config to unreachable DB server
2. Restart backend
3. Visit each of the 5 surfaces
4. Take a screenshot of each (`TC-23-dashboard-nogo.png`, etc.)
5. Assert each screenshot shows a NO-GO banner (red color, `--neg` token)
6. Assert each screenshot includes the text "do not rely on today's board"
7. Assert all 5 screenshots show identical reasons list (DB unavailable)

**Expected outcome:** Induced NO-GO state surfaces on all pages with the required text and consistent reasons.  
**Pass criteria:** All 5 surfaces show NO-GO banner with "do not rely on today's board" and identical reasons; screenshots are md5-distinct from GO and DEGRADED frames.

---

### TC-24 — Journey: Required-still-passing J-01 (evidence badges on leaderboard)

**Type:** browser  
**Preconditions:**
- Frontend and backend running, J-01 deterministic replay script available (`journey-scripts/J-01.json`)

**Steps:**
1. Execute the deterministic J-01 replay script
2. Navigate to `/stocks` and observe leaderboard
3. Assert each row displays an evidence badge (Proven / Not yet proven)
4. Assert the GO banner is present and does not obscure the evidence badges
5. Compare the rendered page to the prior J-01 screenshot; assert no regression in evidence badge visibility

**Expected outcome:** J-01 still passes; evidence badges visible despite new GO banner.  
**Pass criteria:** Replay passes; evidence badges visible on every leaderboard row; GO banner does not overlap or hide badges.

---

### TC-25 — Journey: Required-still-passing J-02 (drill into evidence behind a score)

**Type:** browser  
**Preconditions:**
- Frontend and backend running, J-02 deterministic replay script available

**Steps:**
1. Execute the deterministic J-02 replay script
2. Navigate to `/evidence` and observe the evidence ledger
3. Assert the GO banner is present
4. Assert ledger entries are fully visible and interactive (not obscured by banner)

**Expected outcome:** J-02 still passes; evidence drill-down works despite new banner.  
**Pass criteria:** Replay passes; ledger entries visible and clickable; no regression in evidence page.

---

### TC-26 — Journey: Required-still-passing J-04, J-05, J-11, J-13, J-18 (deterministic replays)

**Type:** browser  
**Preconditions:**
- Frontend and backend running
- Deterministic replay scripts available for all required journeys

**Steps:**
1. Execute each of the 5 journey replay scripts in sequence
2. Record any assertion failures or timeout issues
3. Assert all 5 replays pass

**Expected outcome:** All required journeys still pass; GO banner does not regress existing flows.  
**Pass criteria:** All 5 replay scripts execute successfully with all assertions passing.

---

### TC-27 — Error case: Backend down / health endpoint unavailable

**Type:** browser  
**Preconditions:**
- Frontend running
- Backend stopped or health endpoint returns error (500/503)

**Steps:**
1. Stop the backend service
2. Refresh the frontend at http://localhost:3000/
3. Inspect the banner; assert it renders an honest error state (e.g., "Service unavailable") rather than fabricating a GO
4. Assert the page does not crash and remains interactive (content area still visible)

**Expected outcome:** Banner degrades gracefully when backend is unreachable; no fabricated GO, no blank error page.  
**Pass criteria:** Banner shows a DEGRADED or NO-GO state explaining unavailability; page loads without crashing.

---

### TC-28 — Error case: Empty or unparseable ledger file

**Type:** api  
**Preconditions:**
- Backend running
- Ledger file (canonical, staging, or registry) is corrupted or empty

**Steps:**
1. Truncate or corrupt one ledger file
2. Call `GET /api/health`
3. Assert the response includes a `preflight` field with `verdict` set to DEGRADED or NO-GO (depending on severity config)
4. Assert the `reasons` list includes a phrase explaining the ledger issue
5. Assert no exception is raised; response is valid JSON

**Expected outcome:** Corrupted ledger is gracefully handled; verdict reflects the issue.  
**Pass criteria:** `GET /api/health` returns 200 with honest `verdict` and reasons; no 500 error or exception.

---

### TC-29 — Config: Freshness threshold respected (deterministic, not wall-clock)

**Type:** artifact  
**Preconditions:**
- `config.yaml` contains `readiness.freshness_max_age_days` setting

**Steps:**
1. Read `config.yaml` and verify the `readiness.freshness_max_age_days` value (e.g., 30)
2. Read `app.engine.readiness.py` and verify `compute_preflight()` uses the config value (not a hardcoded number or `date.today()`)
3. Assert the freshness calculation uses the SPY trading-day calendar (reuse of `_cached_warmup_dates` or equivalent)
4. Assert there is no call to `datetime.today()` or `datetime.now()` in the freshness logic

**Expected outcome:** Freshness is config-driven and deterministic, using trading-day calendar.  
**Pass criteria:** Config value is read and applied; no hardcoded literals or wall-clock calls in freshness logic.

---

### TC-30 — Config: No anti-goal #8 violations (no whole-table ORM load on health path)

**Type:** artifact  
**Preconditions:**
- `app/api/health.py` and `app/engine/readiness.py` source code accessible

**Steps:**
1. Read `app/api/health.py` where `compute_preflight()` is called
2. Trace all code paths in `compute_preflight()` for database queries
3. Assert only small-file JSONL reads (ledger file I/O) and no `select(...).all()` or unbounded ORM queries
4. Assert the ledger path resolvers reuse the existing logic (evidence, graveyard, registry path functions)

**Expected outcome:** Health probe uses only small-file I/O; no risk of OOM or slow endpoint.  
**Pass criteria:** No unbounded ORM load paths in `compute_preflight()`; all file reads are for small JSONL ledgers.

---

## Summary

**Total test cases:** 30  
**API tests:** 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-28)  
**Browser tests:** 17 (TC-10, TC-11, TC-12, TC-13, TC-14, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25, TC-26, TC-27)  
**Artifact checks:** 4 (TC-09, TC-15, TC-29, TC-30)  

**Coverage Map:**
- **Backend correctness:** fixture matrix for all input combinations (GO, DEGRADED, NO-GO) with config-wired severity mapping (TC-01–05, 28)
- **Single-source design:** `compute_preflight()` sole producer, served only on `/api/health`, banner reads only provider context (TC-09, 14, 15)
- **Frontend rendering:** GO/DEGRADED/NO-GO states with correct CSS tokens and exact text requirements (TC-11–13)
- **Layout consistency:** banner identical on all 5 required surfaces, all required journeys still pass (TC-16–26)
- **Error handling:** graceful degradation when DB/ledger fails, no fabricated GO, no crashes (TC-27, 28)
- **Anti-goal compliance:** no proven-language, no buy/sell language, no whole-table ORM loads, deterministic freshness (TC-29, 30)
