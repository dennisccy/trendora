# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: P1 smoke tests UT-03 and UT-04 fail; P1 happy-path UT-09 fails -->

**Overall:** 19/25 tests passed (2 skipped, 4 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research hub page loads as a card grid | smoke | P1 | Hub shows 7 named lab cards, no heavy analysis | 7 cards rendered with descriptions, no matrix/chart/table on page, no API calls to research endpoints | PASS | UT-01-result.png |
| UT-02 | Severity-velocity study page loads with matrix | smoke | P1 | Matrix with 3 rows, 3 cols, horizon selector, verdict card | Matrix loaded: Risk-on/Neutral/Risk-off rows, Rising/Flat/Falling cols, horizon selector 1d–60d visible, verdict card present | PASS | UT-02-result.png |
| UT-03 | Factor Lab sub-route loads independently | smoke | P1 | Factor Lab content visible (figures or table) | Page heading "Research — Factor Lab" renders but factor dropdown stuck at "Loading…" indefinitely; no figures or table visible; API returns 500 for `/api/research/factor-lab` with no params (works with params); frontend never populates factor selector | FAIL | UT-03-fail.png |
| UT-04 | Event Study sub-route loads independently | smoke | P1 | Study table or matrix with N= chips visible | Page heading "Research — Setup & Pattern event study" renders; content area shows "Backend unavailable — The event study could not load from the API"; no N= chips; `/api/research/event-study?view=episodes` returns 500 | FAIL | UT-04-fail.png |
| UT-05 | Severity-velocity matrix cell values and horizon selector work | happy-path | P1 | Values change between 5d and 60d horizons | Clicking 5d changed matrix heading to "(5d)" with n=247 for Risk-on/Rising (vs n=241 for 20d default); values confirmed different across horizons | PASS | UT-05-5d.png, UT-05-result.png |
| UT-06 | Verdict card shows honest finding with all three caveats | happy-path | P1 | "NOT supported", "survivorship", "bull-dominated", "underpowered-for-crashes" | All four required phrases confirmed: "NOT supported", "survivorship", "bull-dominated", "preceded a bounce"; "underpowered" phrase present as "underpowered for sustained crashes" (substance met) | PASS | UT-06-result.png |
| UT-07 | N= chip opens reproducing cohort in a new tab | happy-path | P1 | New tab /research/samples shows N count matching chip | Chip link href contains correct kind/horizon/family/velocity_sign params; Samples page shows "Total observations: 241" matching n=241 chip; human-readable cohort desc "Severity-velocity × Regime / Regime family: risk on · Velocity: rising / Horizon: 20d" | PASS | UT-07-result.png |
| UT-08 | Research hub card navigation carries global as-of date | happy-path | P1 | Sub-route URL contains asof=2025-06-30 | Card link href already embeds `?asof=2025-06-30`; after click URL confirmed `http://localhost:3835/research/severity-velocity?asof=2025-06-30` | PASS | UT-08-result.png |
| UT-09 | As-of mode toggle on severity-velocity narrows observations | happy-path | P1 | N values decrease when as-of mode set to 2022-12-31 | Backend API `/api/research/severity-velocity?asof=2022-12-31` returns `asof_date: null` and identical full-history values (n=241 etc.) regardless of asof param; As-of mode UI toggles correctly but data does not narrow | FAIL | UT-09-fail.png |
| UT-10 | Regime-setup-pattern sub-route loads with pre-split figures | regression | P1 | Matrix with numeric values and N= chips | Page "Research — Regime × Setup × Pattern" loaded with N= chips visible | PASS | UT-10-result.png |
| UT-11 | Factor-combination sub-route loads with pre-split figures | regression | P1 | Analysis table with numeric values and N= chips | Page "Research — Multi-factor combination" loaded with N= chips visible | PASS | UT-11-result.png |
| UT-12 | Downtrend-opportunity sub-route loads | regression | P1 | Downtrend analysis table with N= chips | Page "Research — Downtrend Opportunity" loaded with N= chips visible | PASS | UT-12-result.png |
| UT-13 | Recovery-turn-edge sub-route loads | regression | P1 | Recovery-Turn Edge study with N= chips | Page "Research — Recovery-Turn Edge" loaded with N= chips visible | PASS | UT-13-result.png |
| UT-14 | Old /research page no longer shows heavy analysis content | regression | P1 | Hub shows only card grid, no heavy analysis embeds, no research API calls | Hub shows only 7 cards; zero `/api/research/` network calls on hub page load confirmed via performance API | PASS | none |
| UT-15 | Sidebar Research link highlights for any /research/* sub-route | regression | P2 | Research sidebar entry highlighted on /research/event-study | Research link has `aria-current="page"` and `font-medium` class on /research/event-study; only one link active | PASS | none |
| UT-16 | Sidebar Research link highlights for severity-velocity sub-route | regression | P2 | Research sidebar entry highlighted on /research/severity-velocity | Research link has `aria-current="page"` and `font-medium` class; only Research is active | PASS | none |
| UT-17 | Zero-N cells in severity-velocity matrix show NA | validation | P2 | Zero-N cells show NA/low sample, no fabricated numbers | With ?asof=2021-06-30: NA and "low sample" labels present, n=0 cells present, no "Checking backend" skeleton | PASS | none |
| UT-18 | Samples page shows readable description for severity-velocity kind | validation | P2 | Human-readable cohort description on Samples page | Samples page shows "Cohort: Severity-velocity × Regime / Slice: Regime family: risk off · Velocity: rising / Horizon: 20d / Total observations: 180"; not a raw JSON dump | PASS | UT-18-result.png |
| UT-19 | Hub-to-event-study navigation does not trigger other lab fetches | validation | P2 | Only /api/research/event-study call fires | After clicking event-study card from hub, performance API showed only `/api/research/event-study?view=episodes` was requested; no factor-combination, regime-setup-pattern, downtrend-opportunity, or severity-velocity calls | PASS | none |
| UT-20 | Research hub is reachable via sidebar Research link | ux | P2 | Browser navigates to /research showing hub card grid | Sidebar Research link navigated to http://localhost:3835/research; 7 lab cards confirmed visible | PASS | none |
| UT-21 | Severity-velocity lab reachable within 2 clicks from sidebar | ux | P2 | Dashboard sidebar → /research → /research/severity-velocity in 2 clicks | Click 1 (sidebar Research): arrived at /research hub; Click 2 (Severity-velocity card): arrived at /research/severity-velocity with matrix loading | PASS | none |
| UT-22 | Each hub lab card label is clear and matches destination page | ux | P3 | 7 descriptive card labels matching destination headings | All 7 labels confirmed: Factor Lab, Multi-factor combination, Setup & Pattern event study, Regime × Setup × Pattern, Recovery-Turn Edge, Downtrend Opportunity, Severity-velocity × Regime; Factor Lab card → "Research — Factor Lab" heading confirmed | PASS | UT-22-result.png |
| UT-23 | All seven research sub-routes are directly deep-linkable | ux | P2 | All 7 sub-routes return non-404 | All 7 sub-routes return HTTP 200: factor-lab, factor-combination, event-study, regime-setup-pattern, recovery-turn-edge, downtrend-opportunity, severity-velocity | PASS | none |
| UT-24 | Event-study N= chip count coherence after lab relocation | regression | P1 | Samples page count matches N= chip count | SKIPPED — event study API returns 500 consistently; no N= chips are rendered on /research/event-study; cannot verify count coherence | SKIP | UT-04-fail.png |
| UT-25 | Dashboard still loads and charts render after research split | regression | P1 | Dashboard loads with charts and regime label visible | SKIPPED — backend became unresponsive during testing session due to the hung event-study API computation; dashboard showed "Checking backend…" and could not complete load; backend process alive (PID 72189) but all endpoints timing out | SKIP | UT-25-result.png |

---

## Passed Tests

### UT-01 — Research hub page loads as a card grid
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-01-result.png`
- Navigated to /research; page rendered heading "Research" with 7 named lab cards (Factor Lab, Multi-factor combination, Setup & Pattern event study, Regime × Setup × Pattern, Recovery-Turn Edge, Downtrend Opportunity, Severity-velocity × Regime); no matrix, chart, or heavy analysis table present on the hub; zero /api/research/* network calls confirmed

### UT-02 — Severity-velocity study page loads with matrix
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-02-result.png`
- Matrix rendered with 3 rows (Risk-on, Neutral, Risk-off) and 3 columns (Rising Stress, Flat, Falling Stress); cells show mean return, win-rate, n=; horizon selector (1d/5d/10d/20d/60d) present; verdict card present with honest limitations text

### UT-05 — Severity-velocity matrix cell values and horizon selector work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-05-5d.png`
- Default 20d: Risk-on/Rising shows +1.15%, n=241; after clicking 5d: matrix heading changed to "(5d)", Risk-on/Rising shows +0.31%, n=247 — different values confirming horizon switching works without page reload

### UT-06 — Verdict card shows honest finding with all three caveats
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-06-result.png`
- Confirmed: "NOT supported" present; "survivorship" present; "bull-dominated" present; "preceded a bounce, not continuation" present; "underpowered for sustained crashes" present (exact phrase "underpowered-for-crashes" not used but substance identical); no contradictory positive conclusion

### UT-07 — N= chip opens reproducing cohort in a new tab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-07-result.png`
- N= chip link href: `/research/samples?kind=severity-velocity&horizon=20&family=risk_on&velocity_sign=rising`; Samples page shows "Total observations: 241" matching the n=241 chip exactly; human-readable cohort description: "Severity-velocity × Regime / Slice: Regime family: risk on · Velocity: rising / Horizon: 20d"

### UT-08 — Research hub card navigation carries global as-of date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-08-result.png`
- Navigated to /research?asof=2025-06-30; severity-velocity card href confirmed as `/research/severity-velocity?asof=2025-06-30`; after click URL confirmed `http://localhost:3835/research/severity-velocity?asof=2025-06-30`

### UT-10 — Regime-setup-pattern sub-route loads with pre-split figures
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-10-result.png`
- Navigated directly to /research/regime-setup-pattern; page "Research — Regime × Setup × Pattern" loaded with N= chips visible; no 404 or blank page

### UT-11 — Factor-combination sub-route loads with pre-split figures
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-11-result.png`
- Navigated directly to /research/factor-combination; page "Research — Multi-factor combination" loaded with N= chips; no 404 or blank page

### UT-12 — Downtrend-opportunity sub-route loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-12-result.png`
- Navigated directly to /research/downtrend-opportunity; page "Research — Downtrend Opportunity" loaded with N= chips; no 404 or blank page

### UT-13 — Recovery-turn-edge sub-route loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-13-result.png`
- Navigated directly to /research/recovery-turn-edge; page "Research — Recovery-Turn Edge" loaded with N= chips; no 404 or blank page

### UT-14 — Old /research page no longer shows heavy analysis content
**Verdict:** PASS
**Evidence:** none
- Hub page DOM confirmed: no REGIME FAMILY matrix, no RISING STRESS column headers, no decile tables embedded; 7 card links present; performance API confirmed zero /api/research/* calls on hub page load

### UT-15 — Sidebar Research link highlights for any /research/* sub-route
**Verdict:** PASS
**Evidence:** none
- On /research/event-study: Research nav link has `aria-current="page"` and `bg-surface-2 font-medium text-text` classes; only one link active in sidebar

### UT-16 — Sidebar Research link highlights for severity-velocity sub-route
**Verdict:** PASS
**Evidence:** none
- On /research/severity-velocity: Research link has `aria-current="page"` and `font-medium` class; confirmed only Research is highlighted

### UT-17 — Zero-N cells in severity-velocity matrix show NA
**Verdict:** PASS
**Evidence:** none
- With ?asof=2021-06-30: zero-N cells display "NA / low sample" label; no numeric mean return for n=0 cells; no "Checking backend" skeleton persisting

### UT-18 — Samples page shows readable description for severity-velocity kind
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-18-result.png`
- Samples page for kind=severity-velocity&horizon=20&family=risk_off&velocity_sign=rising shows: "Cohort: Severity-velocity × Regime", "Slice: Regime family: risk off · Velocity: rising", "Horizon: 20d", "Total observations: 180"; not a raw JSON dump; no 422 or 500 error

### UT-19 — Hub-to-event-study navigation does not trigger other lab fetches
**Verdict:** PASS
**Evidence:** none
- After navigating from /research hub to /research/event-study: performance entries showed only `/api/research/event-study?view=episodes` — no factor-combination, regime-setup-pattern, downtrend-opportunity, or severity-velocity calls fired

### UT-20 — Research hub is reachable via sidebar Research link
**Verdict:** PASS
**Evidence:** none
- From dashboard: clicked Research in sidebar nav; browser navigated to http://localhost:3835/research; 7 lab card links confirmed

### UT-21 — Severity-velocity lab is reachable within 2 clicks from sidebar
**Verdict:** PASS
**Evidence:** none
- Click 1 from dashboard sidebar → /research (hub with 7 cards); Click 2 on Severity-velocity card → /research/severity-velocity; matrix loaded; total 2 clicks confirmed

### UT-22 — Each hub lab card label is clear and matches destination page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-22-result.png`
- All 7 card labels are descriptive and non-ambiguous; Factor Lab card → "Research — Factor Lab" heading confirmed; Severity-velocity × Regime card → "/research/severity-velocity" confirmed

### UT-23 — All seven research sub-routes are directly deep-linkable
**Verdict:** PASS
**Evidence:** none
- All 7 sub-routes return HTTP 200: factor-lab (200), factor-combination (200), event-study (200), regime-setup-pattern (200), recovery-turn-edge (200), downtrend-opportunity (200), severity-velocity (200)

---

## Failed Tests

### UT-03 — Factor Lab sub-route loads independently
**Verdict:** FAIL
**Failure:** Factor dropdown stuck at "Loading…" indefinitely; no factor figures or table are visible; page renders heading "Research — Factor Lab" but the factor selector never populates so the decile analysis table never appears.

**Steps taken:**
1. Navigated to http://localhost:3835/research/factor-lab
2. Waited 30s for factor dropdown to populate (await_element for select with options)
3. Reloaded the page and waited again
4. Confirmed via eval: `document.querySelectorAll('select')` shows one select with only "Loading…" option
5. Confirmed backend API works via curl: `GET /api/research/factor-lab` (no params) returns valid JSON with factors list and deciles
6. Checked performance entries: two calls to `/api/research/factor-lab` show status "unknown" (fetch in-flight/aborted by React)

**Expected:** Factor Lab page renders factor decile table with figures
**Actual:** Factor dropdown stuck at "Loading…"; no table or figures visible; `document.body.innerHTML` does not contain "Leadership score" despite API returning it; React fetch appears to not resolve in the browser session
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-03-fail.png`

---

### UT-04 — Event Study sub-route loads independently
**Verdict:** FAIL
**Failure:** Event study page renders heading "Research — Setup & Pattern event study" but the content area shows "Backend unavailable — The event study could not load from the API. No figures are shown rather than fabricated values." No N= chips or study table are visible.

**Steps taken:**
1. Navigated to http://localhost:3835/research/event-study
2. Awaited page heading load (confirmed "Research — Setup & Pattern event study")
3. Checked page text: found "Backend unavailable" error message
4. Verified via curl: `GET /api/research/event-study?view=episodes` returns HTTP 500 "Internal Server Error"
5. Attempts to query with subject param (`?subject=vcp&view=episodes`) also timed out (>20s)

**Expected:** Event study page loads with study table and N= chips visible
**Actual:** Page renders structurally but API returns 500; only "Backend unavailable" error message shown; no N= chips rendered
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-04-fail.png`

---

### UT-09 — As-of mode toggle on severity-velocity narrows observations
**Verdict:** FAIL
**Failure:** The severity-velocity backend API ignores the `?asof` parameter. With `asof=2022-12-31`, the API returns `asof_date: null` and identical full-history cell values (n=241, n=356, n=126, etc.) — the same values as the all-history default. The As-of mode UI toggle renders correctly and the page description updates, but the matrix data is not narrowed.

**Steps taken:**
1. Navigated to http://localhost:3835/research/severity-velocity (noted n=241 for Risk-on/Rising as all-history baseline)
2. Navigated to http://localhost:3835/research/severity-velocity?asof=2022-12-31
3. Clicked "As of date" mode button
4. Verified via curl: `GET /api/research/severity-velocity?asof=2022-12-31` returns `{"asof_date": null, ...}` with n=241 (unchanged)

**Expected:** N values decrease with asof=2022-12-31 (fewer observations before that date)
**Actual:** API returns `asof_date: null` regardless of asof parameter; n values identical to all-history (n=241 for Risk-on/Rising)
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/UT-09-fail.png`

---

## Skipped Tests

### UT-24 — Event-study N= chip count coherence after lab relocation
**Verdict:** SKIPPED
**Reason:** Prerequisite not met — event study API returns HTTP 500; no N= chips are rendered on /research/event-study; cannot verify count coherence between chip and Samples page total

### UT-25 — Dashboard still loads and charts render after research split
**Verdict:** SKIPPED
**Reason:** Backend became unresponsive during the testing session due to the hung event-study API computation (PID 72189 alive but consuming 36% CPU/26% RAM, all endpoints timing out); dashboard showed "Checking backend…" permanently and could not complete loading; this is a test-session state issue, not necessarily a code regression

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-22
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-evidence/`
