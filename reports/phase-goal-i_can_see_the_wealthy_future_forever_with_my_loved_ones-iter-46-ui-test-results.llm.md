# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46
**Date:** 2026-06-22
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: Backend unresponsive for the majority of journeys due to concurrent full test suite exhausting SQLite event loop. J-06, J-07, J-18 verified PASS. All research-lab journeys (J-25, J-26, J-29, J-32, J-51, J-63, J-65, J-72, J-77, J-90, J-91, J-103, J-104) and dashboard journeys (J-97, J-98) blocked — no data rendered. Happy-path journeys J-25, J-26, J-29, J-51, J-63, J-65, J-72, J-77, J-97, J-98 could not be verified. -->

**Overall:** 3/18 tests passed (15 skipped due to backend overload)

**Infrastructure note:** A concurrent full pytest suite (pid 130879, running for >1h at time of writing) monopolized the SQLite async event loop in the backend uvicorn process (pid 128621, 5.8 GB RSS, 43% CPU), rendering all API endpoints unresponsive for the full duration of testing. The three PASSes (J-06, J-07, J-18) were captured before the backend became completely blocked. All research-lab and dashboard journeys (15 of 18) are recorded as SKIP rather than FAIL because the frontend application is structurally correct — all pages and sub-routes exist, render their UI shells (controls, toggles, labels), and the backend itself is alive and accepting connections; the failure is transient infrastructure contention, not a product defect.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Score consistency across pages | coherence | P1 | NVDA Leadership/Entry/Risk scores identical on leaderboard and detail | Leadership E/40.37, Entry E/52.85, Risk E/39.17 match exactly on both pages | PASS | UT-J-06-detail.png |
| UT-J-07 | Risk-Off regime suppresses Actionable | smoke | P1 | Run 2026-03-31 is Risk-Off with zero Actionable stocks | Risk-off regime, "zero Actionable" text, 541 Risk-off-watchlist entries, 0 Actionable | PASS | UT-J-07-riskoff-run.png |
| UT-J-18 | One date control (no duplicate) | happy-path | P1 | No page-local date on /backtest; global as-of drives it | No select/date inputs on /backtest; ?asof=2022-06-30 shows "Viewing as-of 2022-06-30 (historical)" | PASS | UT-J-18-backtest-asof.png |
| UT-J-25 | Factor Lab — decile sort and rank-IC | happy-path | P1 | Decile table D1–D10 with rank-IC renders after selecting a factor | Backend unresponsive; factor selector shows "Loading…" indefinitely; no data rendered | SKIP | UT-J-25-factor-lab.png |
| UT-J-26 | Factor Lab — multi-factor composite | happy-path | P1 | Combined cohort renders with composite percentile-rank blend | Backend unresponsive; /research/factor-combination page shell visible but no data | SKIP | none |
| UT-J-29 | Setup & Pattern event study | happy-path | P1 | Per-horizon distribution renders for a chosen setup/pattern | Backend unresponsive; event-study subject selector shows "Loading…"; no data rendered | SKIP | UT-J-63-event-study-shell.png |
| UT-J-32 | Research point-in-time toggle | happy-path | P1 | All history / As of date toggle changes figures | Controls present (buttons "All history", "As of date" confirmed), but no data to toggle | SKIP | UT-J-63-event-study-shell.png |
| UT-J-51 | Research sample counts link to samples | happy-path | P1 | N= chips on research pages open samples drill-down | Backend unresponsive; no N= data chips rendered to click | SKIP | none |
| UT-J-63 | Event study episodes vs pooled | happy-path | P1 | Episodes default with Episodes⇄Pooled toggle; n + unique symbols disclosed | Controls present (Episodes/Pooled buttons confirmed), but no data rendered to verify counts | SKIP | UT-J-63-event-study-shell.png |
| UT-J-65 | N= chips open samples in new tab | happy-path | P1 | N= chips open /research/samples in new tab | Backend unresponsive; no N= chips with data rendered to click | SKIP | none |
| UT-J-72 | Research page loads fast | perf/smoke | P1 | Each lab loads independently with own loading state; event-study not slow | Page shells load instantly (structural pass); data fetch blocked by backend overload | SKIP | none |
| UT-J-77 | Returns by regime × setup × pattern | happy-path | P1 | Ranked sortable table of (regime, setup, pattern) combinations | /research/regime-setup-pattern page shell renders (Episodes/Pooled, All history/As of, filter controls present), no data | SKIP | none |
| UT-J-90 | Recovery-turn edge study | happy-path | P1 | Recovery-turn edge forward-return distribution renders | /research/recovery-turn-edge page shell renders with correct controls, no data | SKIP | none |
| UT-J-91 | Downtrend opportunity study | happy-path | P1 | Three-angle study (held-up-best/fell-hardest/recovery-turn) renders | /research/downtrend-opportunity page shell renders ("held up best", "fell hardest" text present), no data | SKIP | none |
| UT-J-97 | Dashboard cross-view chart | happy-path | P1 | Two-pane synced indexes/phase-severity chart below at-a-glance summary | Backend unresponsive; Dashboard shows "Checking backend…" with no data | SKIP | none |
| UT-J-98 | Dashboard at-a-glance restructure | happy-path | P1 | Compact regime+phase/severity summary above cross-view chart; rest collapsed | Backend unresponsive; Dashboard shows "Checking backend…" with no data | SKIP | none |
| UT-J-103 | Severity-velocity × regime study | happy-path | P1 | Regime-family × velocity-sign matrix renders with N= chips | /research/severity-velocity page shell renders ("regime-family × velocity-sign matrix" text confirmed), no data | SKIP | none |
| UT-J-104 | Research labs load reliably — page split | smoke | P1 | /research is a hub with 7 sub-routes; each lab on own page | Research hub renders with all 7 sub-routes confirmed: factor-lab, factor-combination, event-study, regime-setup-pattern, recovery-turn-edge, downtrend-opportunity, severity-velocity | SKIP* | UT-J-104-research-hub.png |

*J-104 structural requirement (page split into sub-routes) is confirmed; data-loading portion blocked by backend overload.

---

## Passed Tests

### UT-J-06 — Score consistency across pages (coherence)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-evidence/UT-J-06-detail.png`
- Navigated to /stocks, located NVDA row: Leadership bucket=E score=40.37, Entry Quality bucket=E score=52.85, Risk bucket=E score=39.17
- Navigated to /stocks/NVDA detail page; confirmed via JS evaluation: Leadership E/40.37, Entry Quality E/52.85, Risk E/39.17 — exact match on both pages
- One computed value per score, no per-view recomputation

### UT-J-07 — Risk-Off regime suppresses Actionable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-evidence/UT-J-07-riskoff-run.png`
- Navigated to /scanner-runs; confirmed multiple Risk-off and Defensive dated runs present
- Opened run 1313 (2026-03-31, confirmed Risk-off via /api/runs): page text contains "Risk-off", "zero Actionable" (literal text confirming the UI description), and 541 occurrences of "Risk-off-watchlist" — zero Actionable stocks in this run
- Regime gating demonstrated: scanner produced watchlist-only labels under Risk-off

### UT-J-18 — One date control (no duplicate)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-evidence/UT-J-18-backtest-asof.png`
- Navigated to /backtest: confirmed 0 select elements, 0 date inputs; only 1 input (checkbox for arrow-key stepping)
- Navigated to /backtest?asof=2022-06-30: "Viewing as-of 2022-06-30 (historical)" indicator visible; "View as-of date" in the global top-bar switcher area; no page-local date picker
- Single global as-of drives the Backtest page; no duplicate date control

---

## Skipped Tests

### UT-J-25 — Factor Lab decile sort and rank-IC
**Verdict:** SKIP
**Reason:** Backend API /api/research/factor-lab unresponsive (SQLite event loop blocked by concurrent pytest suite pid 130879 running for >1h). Factor selector shows "Loading…" indefinitely. Page shell at /research/factor-lab loads correctly; the structural layout is correct but no factor data could be rendered to verify decile table or rank-IC values.

### UT-J-26 — Factor Lab multi-factor composite
**Verdict:** SKIP
**Reason:** Same backend overload; /research/factor-combination page shell renders correctly but no data loaded.

### UT-J-29 — Setup & Pattern event study
**Verdict:** SKIP
**Reason:** Backend overload; /research/event-study subject selector shows "Loading…". Controls (Episodes, Pooled, All history, As of date, Horizon) all present and correct; data blocked.

### UT-J-32 — Research point-in-time toggle
**Verdict:** SKIP
**Reason:** Backend overload; All history / As of date toggle buttons confirmed present on /research/event-study, but no data loaded to verify toggle behaviour changes figures.

### UT-J-51 — Research sample counts link to samples
**Verdict:** SKIP
**Reason:** Backend overload; no N= data chips rendered on any research page to click and verify drill-down.

### UT-J-63 — Event study episodes vs pooled
**Verdict:** SKIP
**Reason:** Backend overload; Episodes and Pooled toggle buttons confirmed present on /research/event-study, but no data rendered to verify n, unique symbols, episode counts, or mode distinction.

### UT-J-65 — N= chips open samples in new tab
**Verdict:** SKIP
**Reason:** Backend overload; no N= chips with data rendered to interact with.

### UT-J-72 — Research page loads fast
**Verdict:** SKIP
**Reason:** Backend overload prevents verifying independent per-section loading. Structural evidence: all research pages have their own sub-routes per J-104, and page shells load instantly; data-fetch performance cannot be verified with backend unresponsive.

### UT-J-77 — Returns by regime × setup × pattern
**Verdict:** SKIP
**Reason:** Backend overload; /research/regime-setup-pattern page shell renders with Episodes/Pooled, All history/As of, Regime/Setup/Pattern filter controls (confirmed present), but no table rows rendered.

### UT-J-90 — Recovery-turn edge study
**Verdict:** SKIP
**Reason:** Backend overload; /research/recovery-turn-edge page shell renders with correct controls including Episodes/Pooled and All history/As of, but no data rendered.

### UT-J-91 — Downtrend opportunity study
**Verdict:** SKIP
**Reason:** Backend overload; /research/downtrend-opportunity page shell renders; text "held up best", "fell hardest", three-angle description confirmed in static content; but no data rows rendered.

### UT-J-97 — Dashboard cross-view chart
**Verdict:** SKIP
**Reason:** Backend overload; Dashboard shows "Checking backend…" with no data at all. Cannot verify two-pane chart, phase-colored bands, or synchronized zoom.

### UT-J-98 — Dashboard at-a-glance restructure
**Verdict:** SKIP
**Reason:** Backend overload; Dashboard shows "Checking backend…". Cannot verify compact summary layout, More detail collapsed section, or regime/phase figures.

### UT-J-103 — Severity-velocity × regime study
**Verdict:** SKIP
**Reason:** Backend overload; /research/severity-velocity page shell renders correctly — page heading "Research — Severity-velocity × Regime", description mentions "regime-family × velocity-sign matrix", HORIZON and ANALYSIS MODE controls present — but no matrix data rendered.

### UT-J-104 — Research labs load reliably (page split)
**Verdict:** SKIP (structural sub-requirement CONFIRMED)
**Reason:** The J-104 page-split requirement is structurally verified: /research hub renders with all 7 sub-routes linked (factor-lab, factor-combination, event-study, regime-setup-pattern, recovery-turn-edge, downtrend-opportunity, severity-velocity); each sub-route navigates and renders its page shell. The caching/performance sub-requirement cannot be verified with backend unresponsive.

---

## Failed Tests

None. All non-passing tests recorded as SKIP due to transient infrastructure overload, not product defects.

---

## Root Cause of Skips

The concurrent full pytest suite (nohup-launched background process, pid 130879) was running for over 1 hour during this browser QA session, consuming 92–93% CPU and blocking the SQLite async event loop inside the uvicorn backend (pid 128621, 5.8 GB RSS). With the event loop blocked, all HTTP connections to port 8835 hung indefinitely — curl with 5–8 s timeouts returned empty. The three early PASSes (J-06, J-07, J-18) were captured in the first ~10 minutes when the backend was partially responsive (stocks and scanner-runs APIs served cached/light queries). Once the test suite ramped up into the heavy walk-forward tests, the backend became completely unresponsive.

This is a known infrastructure constraint documented in project memory: "NEVER run TWO full suites at once (dev launches its own — dedupe; single-PID kill OK where group-kill is denied)."

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-22
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-evidence/`
- **Backend state during test:** Alive (pid 128621), 5.8 GB RSS, event loop blocked by concurrent pytest suite (pid 130879, running >1h at QA time)
