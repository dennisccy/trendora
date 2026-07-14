# Phase goal-mcp-loop-iter-33 — UI Test Plan

**Phase:** goal-mcp-loop-iter-33 (J-20 — Daily Preflight Verdict, backlog B-301)
**Date:** 2026-07-14
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (the paired backend port for this run — `start-frontend.sh`/`start-backend.sh` both apply the same `+255` offset to their 3000/8000 defaults; confirmed by the dev handoff's own live-testing port pair)

---

## Scope note

This phase adds exactly one new visible element — a read-only status strip (`PreflightBanner`,
`data-testid="preflight-banner"`) mounted once in the shared app shell — that shows one of four states:
a neutral loading placeholder, a quiet green `GO`, a loud amber `DEGRADED`, or a loud red `NO-GO`. It has
no buttons, forms, or links, so several of the skill's usual "validation" (form) scenarios do not apply;
those slots below are repurposed for the closest honest equivalent (the banner never *fabricates* a
healthy state, and its reason text is specific rather than generic). This plan covers the UI/browser
surface only — it does not repeat the backend fixture-matrix, config-wiring, or artifact/grep checks
already covered as TC-01–TC-09/TC-28–TC-30 in `reports/qa/goal-mcp-loop-iter-33-test-plan.md`.

**Priority overrides vs. the generic skill defaults:** several `error`/`validation`/`regression` cases
below are marked **P1** rather than the skill's default P2/P3, because the phase's own Definition of Done
makes them hard must-pass criteria, not optional extras:
- The induced `DEGRADED` and `NO-GO` checks (UT-13, UT-14) are literally "DoD Step 2."
- The backend-unreachable honest-fallback check (UT-12) and the never-fabricate-GO check (UT-15) enforce
  anti-goal #8 (critical: no blank crash, no fabricated healthy state).
- The existing readiness badge byte-identity check (UT-09) and the evidence/leaderboard regression check
  (UT-10) protect J-40 and the explicitly named "Required-still-passing" journeys J-01/J-02.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads with the quiet GO banner (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend running and reachable at `http://localhost:8255`; frontend running at `http://localhost:3255`
- Backend is using its normal, unmodified `config.yaml` (no freshness/ledger overrides in effect) against
  the committed seed data — this is the default "healthy" state
- No login is required (Trendora is a local-first, single-user tool)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to finish loading (a brief neutral "Checking board status…" flash, if seen at all, should disappear within a couple of seconds)

**Expected Result:**
- The heading "Dashboard" is visible
- Directly below the header bar (below the "Research-only · decision support · no orders" text and the readiness badge in the top-right) a thin single-line strip is visible reading exactly: **"GO — today's board is current."** with a small green dot to its left
- The strip shows no bulleted reasons (GO has none)
- No error message, blank screen, or crash

---

### UT-02 — `/stocks` loads with the same GO banner above the leaderboard (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to finish loading

**Expected Result:**
- The heading "Stocks" is visible
- The identical thin strip "GO — today's board is current." with a green dot appears directly below the header, above the stock leaderboard table
- The leaderboard table still loads with ticker rows visible beneath the strip

---

### UT-03 — Stock detail page loads with the GO banner (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/NVDA`

**Preconditions:** Same as UT-01; NVDA exists in the seed universe

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA`
2. Wait for the page to finish loading

**Expected Result:**
- The heading "NVDA" is visible
- The identical "GO — today's board is current." strip appears directly below the header
- The stock detail content beneath it (the three scores, the "Not yet proven" evidence badge, the price chart) still renders normally, with no visual overlap between the strip and the page content

---

### UT-04 — `/watchlist` loads with the GO banner (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:** Same as UT-01. The watchlist may be empty (no saved stocks) — this is expected and unrelated to the banner.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Wait for the page to finish loading

**Expected Result:**
- The heading "Watchlist" is visible
- The identical "GO — today's board is current." strip appears directly below the header
- Beneath it, either the watchlist table or the empty-state message "Your watchlist is empty" is fully visible, not obscured by the strip

---

### UT-05 — `/evidence` loads with the GO banner (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to finish loading

**Expected Result:**
- The heading "Evidence" is visible
- The identical "GO — today's board is current." strip appears directly below the header
- The certified-claims ledger table beneath it is fully visible

---

### UT-06 — GO banner is identical on every required decision surface (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/` and note the banner's exact text and color
2. Navigate to `http://localhost:3255/stocks` and compare the banner to step 1
3. Navigate to `http://localhost:3255/stocks/NVDA` and compare
4. Navigate to `http://localhost:3255/watchlist` and compare
5. Navigate to `http://localhost:3255/evidence` and compare

**Expected Result:**
- On all five pages the banner reads the exact same text: "GO — today's board is current."
- On all five pages the banner is the same thin, quiet, green-tinted strip in the same position (directly below the header, above the page's own content) — no page shows different wording, color, or size
- This is the core new capability under test: one glance at any decision surface tells the user the board is safe to trust, with no page-specific behavior

---

### UT-07 — `/research` and a research sub-page inherit the same banner (happy path / coverage)

**Type:** happy-path
**Priority:** P2 (not one of the DoD's five required surfaces, but explicitly named in goal.md's "UI surface changes"; the dev handoff's live-verification log did not independently screenshot this route)
**Surface:** `/research`, `/research/factor-lab`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Confirm the "GO — today's board is current." strip is visible below the header, above the "Research" heading and its list of labs
3. Navigate to `http://localhost:3255/research/factor-lab`
4. Wait for the page to finish loading

**Expected Result:**
- Step 2: the identical GO strip is visible on `/research`
- Step 4: the identical GO strip is still visible on `/research/factor-lab`, same position, same text, same color

---

### UT-08 — Banner appears on every remaining nav page without colliding with existing page elements (happy path / coverage)

**Type:** happy-path
**Priority:** P2
**Surface:** `/sectors`, `/themes`, `/backtest`, `/methodology`, `/scanner-runs`, `/data`

**Preconditions:** Same as UT-01

**Steps:**
1. Using the left sidebar, click "Sectors", then "Themes", then "Backtest", then "Methodology", then "Scanner Runs" in turn, checking each page after it loads
2. For each page in step 1, confirm the "GO — today's board is current." strip appears below the header before checking the page's own content
3. Click "Data Manager" in the sidebar to open `http://localhost:3255/data`
4. Look at the top of the page, immediately below the new GO strip

**Expected Result:**
- Steps 1–2: every page shows the identical GO strip; none of the pages crash or show a blank screen
- Step 4: the new "GO — today's board is current." strip and `/data`'s own pre-existing page content are visually distinct and do not overlap — the GO strip is a thin single line directly under the header; any of `/data`'s own status elements sit further down, inside the page body, clearly separate from the new strip

---

### UT-09 — Existing readiness badge (top-right of header) is unchanged by the new banner (regression)

**Type:** regression
**Priority:** P1 (the phase spec explicitly requires `compute_readiness`'s `state`/`warmup` output — which this badge displays — to stay byte-identical; "J-40 not regressed" is named repeatedly in the Definition of Done)
**Surface:** header (all pages)

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Look at the top-right of the header bar, to the right of the as-of date control

**Expected Result:**
- A pill-shaped badge reading "Ready" with a small solid green dot is visible — this is the pre-existing readiness badge, a separate element from the new banner strip beneath the header
- Badges reading "provider: `<name>`", "seed `<date>`", and "`<N>` symbols" still appear beside it, exactly as before this phase
- Nothing about this badge's text, color, or position has changed by this phase

---

### UT-10 — Evidence badges and leaderboard content are unaffected by the new banner (regression — J-01/J-02 required-still-passing)

**Type:** regression
**Priority:** P1 (J-01 and J-02 are explicitly listed in the phase spec's "Required-still-passing journeys")
**Surface:** `/stocks`, `/evidence`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at several rows in the leaderboard table, below the new GO strip
3. Navigate to `http://localhost:3255/evidence`
4. Look at the ledger table, below the new GO strip

**Expected Result:**
- Step 2: each leaderboard row still shows its evidence badge (reading "Not yet proven" against today's ledger), fully visible and not hidden or cut off by the strip above it
- Step 4: the evidence ledger table's rows (each showing a "FAIL" status per the current ledger state) are still fully visible and readable, unaffected by the strip above the table

---

### UT-11 — Page content is fully visible beneath the banner on both a quiet and a loud day (regression / layout)

**Type:** regression
**Priority:** P2
**Surface:** `/`, `/stocks/NVDA`

**Preconditions:** UT-01 (GO) and UT-13 or UT-14 (DEGRADED/NO-GO) have been performed so both states are available to compare

**Steps:**
1. With the backend healthy (GO), navigate to `http://localhost:3255/` and note where the dashboard's own first content block begins, just below the thin GO strip
2. Trigger the DEGRADED or NO-GO state (per UT-13/UT-14), then reload `http://localhost:3255/`
3. Compare where the dashboard's own first content block begins now, below the taller loud banner

**Expected Result:**
- In both cases, all dashboard content is fully visible and readable — nothing is cut off, hidden behind the banner, or requires extra scrolling to reach that wasn't needed before this phase
- On the DEGRADED/NO-GO day the content starts a little further down than on the GO day, because the loud banner is taller — this is expected, spec-required behavior, not a defect. The failure case would be content actually hidden behind or overlapping the banner, not simply shifted down

---

### UT-12 — Backend fully unreachable shows an honest NO-GO fallback, never a blank page (error)

**Type:** error
**Priority:** P1 (anti-goal #8: a failed/unavailable data path must degrade honestly, never a blank crash page or a fabricated healthy state)
**Surface:** `/` (representative; applies to every page)

**Preconditions:** Frontend running; terminal/shell access to stop and restart the backend process (`scripts/start-backend.sh` or `scripts/dev.sh`)

**Steps:**
1. With the app open at `http://localhost:3255/` in a healthy GO state, stop the backend process entirely
2. Without touching the browser tab, wait up to 30 seconds (or refresh the page for an immediate check)

**Expected Result:**
- The page does NOT go blank and does NOT show a browser/JS crash screen
- The strip below the header switches to a full-width red banner with the bold headline: **"NO-GO — do not rely on today's board."**
- Below the headline, exactly one bulleted reason reads: **"Backend is unavailable — the preflight check could not run."**
- The rest of the page (sidebar, header chrome) remains visible
- Restart the backend afterward and confirm the strip returns to the quiet green "GO — today's board is current." within 30 seconds, or immediately on refresh

---

### UT-13 — Induced DEGRADED verdict shows the amber banner with a concrete reason on every required surface (error — DoD Step 2)

**Type:** error
**Priority:** P1 (Definition of Done, Step 2: "under the controlled inducement, EVERY listed surface shows the SAME DEGRADED/NO-GO banner with the concrete reasons")
**Surface:** `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`

**Preconditions:** Terminal/shell access to restart the backend with a config override, without touching the committed seed data. The default config maps a freshness breach to `DEGRADED` (`readiness.severity.freshness: degraded`) and its default threshold is `readiness.freshness_max_age_days: 5`; pointing `TRENDORA_CONFIG` at a copy of `config.yaml` with that value set to a negative number (e.g. `-1`) forces a breach.

**Steps:**
1. Stop the backend
2. Restart it with the freshness threshold overridden to a negative value (per Preconditions) — do not modify the committed seed data
3. Navigate to (or refresh) `http://localhost:3255/`
4. Repeat for `http://localhost:3255/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`

**Expected Result:**
- On every one of the five pages, the strip switches from the thin green line to a full-width amber banner
- The bold headline on every page reads exactly: **"DEGRADED — treat today's board with caution."**
- Below the headline, a bulleted reason is visible matching the pattern: "Latest data (`<date>`) is 0 trading day(s) old, exceeding the configured maximum of `<threshold>` day(s)." — the date shown should match the "seed `<date>`" value already visible in the existing readiness badge (top-right of header)
- All five pages show the identical headline and identical reason text
- Restore the original config and restart the backend; confirm all five pages return to "GO — today's board is current." afterward

---

### UT-14 — Induced NO-GO verdict contains the exact mandated phrase on every required surface (error — DoD Step 2, critical)

**Type:** error
**Priority:** P1 (Definition of Done + goal.md acceptance: the NO-GO banner must contain the exact phrase "do not rely on today's board")
**Surface:** `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`

**Preconditions:** Terminal/shell access to restart the backend with `TRENDORA_LEDGER_PATH` pointed at a path that does not exist — do not delete or modify any real ledger file. The default config maps an integrity breach to `NO-GO` (`readiness.severity.integrity: no-go`).

**Steps:**
1. Stop the backend
2. Restart it with `TRENDORA_LEDGER_PATH` pointed at a nonexistent file path (per Preconditions)
3. Navigate to (or refresh) `http://localhost:3255/`
4. Repeat for `http://localhost:3255/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence`

**Expected Result:**
- On every one of the five pages, the strip switches to a full-width red banner
- The bold headline on every page reads exactly: **"NO-GO — do not rely on today's board."**
- Below the headline, a bulleted reason mentions the missing ledger file — text containing "Integrity check failed" and "missing"
- All five pages show the identical headline and identical reason text
- Restore the original `TRENDORA_LEDGER_PATH` (or unset it) and restart the backend; confirm all five pages return to "GO — today's board is current." afterward

---

### UT-15 — First load never shows a fabricated GO before the check completes (validation)

**Type:** validation
**Priority:** P1 (anti-goal #8: the banner must never claim a trust status before it has actually verified one — a premature "GO" would be exactly the fabricated-success case anti-goal #8 forbids)
**Surface:** `/` (representative; applies to every page)

**Preconditions:** Chrome DevTools available (F12) — a standard browser feature, not a code-level tool

**Steps:**
1. Open Chrome DevTools (F12), open the Network tab, and set throttling to "Slow 3G"
2. Navigate to `http://localhost:3255/` (or hard-refresh with throttling already active)
3. Immediately look at the strip below the header, before the page finishes loading

**Expected Result:**
- Before the first health check resolves, the strip is gray/neutral and reads exactly: **"Checking board status…"** — it does NOT show a green GO line or any colored verdict yet
- Once the first check resolves, the strip updates to the real verdict (GO/DEGRADED/NO-GO depending on backend state) — it never jumps straight to a green GO without first showing the neutral checking state
- Set throttling back to "Online" afterward

---

### UT-16 — DEGRADED/NO-GO reasons are specific and actionable, never generic (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:** A DEGRADED or NO-GO state has been induced (per UT-13 or UT-14)

**Steps:**
1. With the backend in the induced DEGRADED or NO-GO state, navigate to `http://localhost:3255/`
2. Read the bulleted reason(s) below the banner headline

**Expected Result:**
- The reason text names the specific problem (e.g. the exact number of trading days stale and the configured maximum, or the specific missing file/path) — not a generic phrase like "Something went wrong" or "Error occurred"
- A reader with no technical background can tell roughly why the board should not be trusted today from the sentence alone

---

### UT-17 — Verdict updates live without a manual page refresh (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/`

**Preconditions:** Page open and showing GO; terminal/shell access to induce DEGRADED (per UT-13)

**Steps:**
1. Open `http://localhost:3255/` and confirm the banner reads "GO — today's board is current."
2. Without refreshing or closing the browser tab, induce the DEGRADED state on the backend (per UT-13's steps 1–2)
3. Watch the still-open tab for up to 30 seconds without touching it

**Expected Result:**
- The banner automatically switches from the green GO strip to the amber DEGRADED banner within the wait window, with no page refresh or other user action required
- This confirms the verdict is polled live, not fetched once at initial page load and then left stale

---

### UT-18 — Banner is self-explanatory with no click or hover required (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/` as a first-time user would, without reading any documentation
2. Look at the strip below the header without clicking or hovering over anything

**Expected Result:**
- The meaning is clear from the text alone ("GO — today's board is current.") — no click, hover, tooltip, or explanation is needed to understand today's board is trustworthy
- The strip does not look clickable (no pointer-cursor affordance, no button/link styling) — it reads as status information, consistent with the product never presenting a buy/sell action

---

### UT-19 — Exactly one banner exists per page, fed by a single check (ux / single-source)

**Type:** ux
**Priority:** P3
**Surface:** `/`, `/stocks`

**Preconditions:** Chrome DevTools available (F12)

**Steps:**
1. Navigate to `http://localhost:3255/`, open DevTools → Elements, and search (Ctrl+F in the Elements panel) for `data-testid="preflight-banner"`
2. Open DevTools → Network tab, filter by "health", and watch for about 10 seconds
3. Navigate to `http://localhost:3255/stocks` and repeat both checks

**Expected Result:**
- Exactly one element with `data-testid="preflight-banner"` exists in the page at any time — never zero, never duplicated
- Only one request to `/api/health` appears per poll cycle — no second/duplicate request fires from the banner itself; it shares the same single check the existing readiness badge already uses

---

### UT-20 — No new navigation item was added for the banner (ux)

**Type:** ux
**Priority:** P3
**Surface:** sidebar (all pages)

**Preconditions:** Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Look at the left sidebar's full list of items

**Expected Result:**
- The sidebar shows exactly the same 11 items as before this phase: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager
- No new nav item (e.g. "Preflight" or "Status") was added — the verdict lives inside the existing page shell as chrome, not as a destination you navigate to

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with GO banner | smoke | P1 | `/` |
| UT-02 | `/stocks` loads with GO banner | smoke | P1 | `/stocks` |
| UT-03 | Stock detail loads with GO banner | smoke | P1 | `/stocks/NVDA` |
| UT-04 | `/watchlist` loads with GO banner | smoke | P1 | `/watchlist` |
| UT-05 | `/evidence` loads with GO banner | smoke | P1 | `/evidence` |
| UT-06 | GO banner identical on all 5 required surfaces | happy-path | P1 | `/`, `/stocks`, `/stocks/NVDA`, `/watchlist`, `/evidence` |
| UT-07 | `/research` + sub-page inherit banner | happy-path | P2 | `/research`, `/research/factor-lab` |
| UT-08 | Remaining nav pages show banner, no collision on `/data` | happy-path | P2 | `/sectors`, `/themes`, `/backtest`, `/methodology`, `/scanner-runs`, `/data` |
| UT-09 | Existing readiness badge unchanged | regression | P1 | header (all pages) |
| UT-10 | Evidence badges / leaderboard unaffected (J-01/J-02) | regression | P1 | `/stocks`, `/evidence` |
| UT-11 | Content fully visible on quiet and loud days | regression | P2 | `/`, `/stocks/NVDA` |
| UT-12 | Backend down → honest NO-GO fallback, no blank page | error | P1 | `/` |
| UT-13 | Induced DEGRADED shows amber banner + reason (DoD Step 2) | error | P1 | 5 required surfaces |
| UT-14 | Induced NO-GO shows exact mandated phrase (DoD Step 2) | error | P1 | 5 required surfaces |
| UT-15 | First load never fabricates GO | validation | P1 | `/` |
| UT-16 | DEGRADED/NO-GO reasons are specific, not generic | validation | P2 | `/` |
| UT-17 | Verdict updates live without refresh | happy-path | P2 | `/` |
| UT-18 | Banner is self-explanatory, no click needed | ux | P3 | `/` |
| UT-19 | Exactly one banner, single-source | ux | P3 | `/`, `/stocks` |
| UT-20 | No new nav item added | ux | P3 | sidebar |

**P1 tests must all pass for browser QA verdict to be PASS.**
