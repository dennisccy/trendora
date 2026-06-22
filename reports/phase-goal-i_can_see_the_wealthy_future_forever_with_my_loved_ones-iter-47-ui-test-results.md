# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 14/19 tests passed (0 skipped, 5 failed)

P1 failures: UT-04, UT-05, UT-06 (Factor Lab — Backend unavailable / MemoryError); UT-15 (Factor Lab portion of N= coherence cross-lab check); UT-19 (Factor Lab does not load independently).

Root cause: `apps/backend/app/engine/research.py` line 216 — `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` is an unbounded full-ORM read on 609,166 ScannerResult rows that was NOT converted to a streamed/projected read by the iter-47 refactor (only `ForwardReturn` reads were streamed). Under live-dataset load the process raises `MemoryError`, causing HTTP 500 on every `/api/research/factor-lab` request.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Event-Study matrix loads without errors | smoke | P1 | Matrix with numeric values, no skeleton/error | Matrix fully populated: 5 horizon rows (1d–60d) all with numeric mean_return, win-rate, N | PASS | `UT-01-result.png` |
| UT-02 | Event-Study per-horizon mean/win-rate/N render | happy-path | P1 | 5d row: numeric mean, win-rate, N>0; 2+ other rows | 5d: +0.47% mean, 57.99% win-rate, N=457; all 5 horizons populated | PASS | `UT-01-result.png` |
| UT-03 | Event-Study N= drill-down is count-coherent | happy-path | P1 | /research/samples total = N on chip | 20d chip showed N=455; /research/samples showed "Total observations: 455" | PASS | `UT-03-result.png` |
| UT-04 | Factor Lab decile table and rank-IC render | smoke | P1 | Decile table with numeric values, no skeleton/error | "Backend unavailable" message — HTTP 500 MemoryError on `/api/research/factor-lab` | FAIL | `UT-04-fail.png` |
| UT-05 | Factor Lab 10 decile rows with real figures | happy-path | P1 | 10 decile rows with numeric mean_return | Decile table never renders; Factor Lab shows "Backend unavailable" | FAIL | `UT-04-fail.png` |
| UT-06 | Factor Lab N= drill-down is count-coherent | happy-path | P1 | N= chip click → /research/samples count matches | N= chips never appear; Factor Lab fails to load | FAIL | `UT-04-fail.png` |
| UT-07 | Factor-combination composite cohort renders real figures | happy-path | P1 | pool_n > 0, composite row with numeric mean_return and win-rate | pool_n=598,271; composite and per-condition rows all show numeric values | PASS | `UT-07-result.png` |
| UT-08 | Regime x Setup x Pattern table loads without errors | smoke | P1 | Ranked table with real rows, no error banner | Table fully populated with 100+ rows, numeric mean_return and n_total throughout | PASS | `UT-08-result.png` |
| UT-09 | Regime x Setup x Pattern rows have numeric mean_return and n_total | happy-path | P1 | 3+ rows with regime label, numeric mean_return, non-zero n | First row: Defensive / Actionable / —(none) / n=51 / +5.66% / 82.35% hit-rate | PASS | `UT-08-result.png` |
| UT-10 | Downtrend Opportunity loads without errors | smoke | P1 | Page renders with at least one row with numeric mean_return | "Held up best" table: Expansion n=591 +5.18%, Recovery n=103 +5.09% etc. | PASS | `UT-10-result.png` |
| UT-11 | Downtrend Opportunity shows real figures within 30 seconds | happy-path | P1 | Data appears within 30s on warm cache | Data appeared immediately on warm cache; Expansion row +5.18% 74.28% hit-rate | PASS | `UT-10-result.png` |
| UT-12 | Low-sample horizons show honest NA/partial state | error | P2 | NA + n shown for <30 sample cohorts, real values for ≥30 | By-regime: Strong risk-on n=11 → NA; Risk-off n=0 → NA; Risk-on n=80 → +0.55% real value | PASS | `UT-01-result.png` |
| UT-13 | /research/samples without params shows handled empty state | error | P2 | Handled empty state, no crash/500 | Page shows "Unknown sample cohort — Return to Research and click an N= figure" | PASS | none |
| UT-14 | All five Research labs reachable from navigation hub | regression | P1 | All sub-routes load from Research hub navigation | /research/event-study, /research/regime-setup-pattern, /research/downtrend-opportunity all load without error; hub links for all 7 labs confirmed | PASS | none |
| UT-15 | N= count coherence holds across multiple labs | regression | P1 | N on chip = total on /research/samples for both event-study and factor-lab | Event-study N=455 → samples 455 (PASS); Factor Lab portion blocked — Factor Lab returns 500, N= chips never appear | FAIL | `UT-03-result.png` |
| UT-16 | NVDA leaderboard scores match detail page | regression | P1 | Leadership/Entry Quality/Risk identical on leaderboard and detail | Leaderboard: 40.37 / 52.85 / 39.17 — Detail: 40.37 / 52.85 / 39.17 — exact match | PASS | none |
| UT-17 | As-of date toggle still works after backend refactor | regression | P1 | Historical date shows different figures; return to latest restores current | ?asof=2026-05-15 → regime 68.03 / Pullback phase; latest → 73.44 / Risk-on / Expansion | PASS | `UT-17-asof-panel.png` |
| UT-18 | Research section discoverable from main navigation | ux | P2 | "Research" link in main nav, sub-labs visible on hub | "Research" is always in sidebar; hub page lists all 7 sub-labs with descriptions and links | PASS | `UT-18-nav.png` |
| UT-19 | Five heavy labs load independently without interfering | ux | P2 | Each lab loads real data one-at-a-time without blocking others | Event-study: PASS; Factor Lab: FAIL (MemoryError); Regime-setup-pattern: PASS; Downtrend-opportunity: PASS; factor-combination: PASS | FAIL | `UT-04-fail.png` |

---

## Passed Tests

### UT-01 — Event-Study matrix loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-01-result.png`
- Navigated to http://localhost:3835/research/event-study; page heading "Research — Setup & Pattern event study" visible
- Matrix immediately populated (warm cache) with 5 horizon rows: 1d, 5d, 10d, 20d, 60d
- All rows show numeric mean_return, win-rate, N — no skeleton, no "Backend unavailable" message

---

### UT-02 — Event-Study per-horizon mean/win-rate/N render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-01-result.png`
- 5d row: N=457, mean=+0.47%, median=+0.65%, %-positive=57.99%, MEAN MAE=-2.12%, MEAN MFE=+2.50%
- 10d row: N=457, mean=+0.91%, 58.64% positive
- 20d row (best exit): N=455, mean=+1.75%, 63.30% positive
- 60d row: N=445, mean=+1.54%

---

### UT-03 — Event-Study N= drill-down is count-coherent
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-03-result.png`
- 20d N= chip shows N=455 in the matrix
- Navigated to /research/samples?kind=event-study&horizon=20&subject=Actionable&slice=pooled&view=episodes
- Page shows "Total observations: 455" — exact match with chip value

---

### UT-07 — Factor-combination composite cohort renders real figures
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-07-result.png`
- Navigated to http://localhost:3835/research/factor-combination
- Baseline (all names): N=598,271, +0.88% mean, 52.89% hit-rate
- Combined (composite rank-blend): N=119,655, +0.24% mean, 51.49% hit-rate
- All cohort rows rendered with numeric values; no "Backend unavailable" or loading state

---

### UT-08 — Regime x Setup x Pattern table loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-08-result.png`
- Navigated to http://localhost:3835/research/regime-setup-pattern
- Table populated with 100+ rows; first row: Defensive / Actionable / —(none) / n=51 / +5.66%
- No error banner; low-sample rows correctly show NA + n⚠

---

### UT-09 — Regime x Setup x Pattern rows have numeric mean_return and n_total
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-08-result.png`
- First 3 rows with n≥30: Defensive/Actionable/—(none) n=51 +5.66%, Defensive/Extended/pullback n=48 +5.41%, Narrow leadership/Actionable/pullback n=76 +3.20%
- All rows with n≥30 show numeric mean_return, median, hit-rate, expectancy, MDD, risk-adjusted ratios

---

### UT-10 — Downtrend Opportunity loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-10-result.png`
- Navigated to http://localhost:3835/research/downtrend-opportunity
- "Held up best" table: Expansion n=591 +5.18% 74.28%, Recovery n=103 +5.09% 52.43%
- Recovery-turn edge by phase section also populated; no error message

---

### UT-11 — Downtrend Opportunity shows real figures within 30 seconds
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-10-result.png`
- Data appeared immediately (warm cache) — well within 30 seconds
- No "Backend unavailable" message at any point during load

---

### UT-12 — Low-sample horizons show honest NA/partial state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-01-result.png`
- By-regime (20d): Strong risk-on n=11 ⚠ → NA NA NA; Risk-off n=0 ⚠ → NA NA NA
- By-sector (20d): Technology n=3 ⚠, Financials n=3 ⚠ etc. all show NA + n
- Risk-on n=80 (above threshold) shows real value +0.55% 56.25%

---

### UT-13 — /research/samples without params shows handled empty state
**Verdict:** PASS
**Evidence:** none (page text sufficient)
- Navigated to http://localhost:3835/research/samples (no query params)
- Page shows: "Unknown sample cohort — This drill-down link does not describe a valid research cohort. Return to Research and click an N= figure to open its samples."
- No 500 error, no blank white screen, no crash

---

### UT-14 — All five Research labs reachable from navigation hub
**Verdict:** PASS
**Evidence:** none
- /research hub lists 7 lab links: Factor Lab, Multi-factor combination, Setup & Pattern event study, Regime × Setup × Pattern, Recovery-Turn Edge, Downtrend Opportunity, Severity-velocity × Regime
- /research/event-study, /research/regime-setup-pattern, /research/downtrend-opportunity each loaded successfully with heading rendered

---

### UT-16 — NVDA leaderboard scores match detail page
**Verdict:** PASS
**Evidence:** none (scores extracted from page text)
- Leaderboard (/stocks): NVDA Leadership=40.37, Entry Quality=52.85, Risk=39.17
- Detail (/stocks/NVDA): Leadership=40.37, Entry Quality=52.85, Risk=39.17
- Digit-for-digit identical; page subtitle says "identical to the leaderboard; single source of truth"

---

### UT-17 — As-of date toggle still works after backend refactor
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-17-asof-panel.png`
- Navigated to http://localhost:3835/?asof=2026-05-15; dashboard shows "Viewing as-of 2026-05-15 (historical)", regime score 68.03, phase=Pullback
- Navigated to http://localhost:3835/ (no asof); dashboard shows "Data as-of 2026-06-16", regime score 73.44, phase=Expansion
- Also verified step-back button: clicking once stepped from 2026-06-16 → 2026-06-15 with score change 73.44→73.26

---

### UT-18 — Research section discoverable from main navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-18-nav.png`
- "Research" link is always visible in the sidebar on every page (Dashboard, Stocks, etc.)
- Clicking navigates to http://localhost:3835/research which shows all 7 lab entries with description cards and direct links — no hidden menus required

---

## Failed Tests

### UT-04 — Factor Lab decile table and rank-IC render
**Verdict:** FAIL
**Failure:** The Factor Lab page at http://localhost:3835/research/factor-lab shows "Backend unavailable — The Factor-Lab evidence could not load from the API" on every load attempt. The backend returns HTTP 500 on `/api/research/factor-lab`.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-04-fail.png`

**Root cause (from backend log `/tmp/fanout-backend-8835.log`):**
```
MemoryError
...
File "apps/backend/app/engine/research.py", line 216, in _factor_observations
    session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
MemoryError
```
The `_factor_observations` function loads 609,166 ScannerResult rows via an unbounded `.all()` ORM call (line 216 of `research.py`). The iter-47 refactor converted `ForwardReturn` reads to `yield_per` streaming, but this `ScannerResult` read was left as a full `.all()`. Under the live 3.3 GB dataset with the background test suite consuming RAM, this raises `MemoryError` every time.

**Steps taken:**
1. Navigated to http://localhost:3835/research/factor-lab
2. Waited 60 seconds — page shows "Loading…" for FACTOR selector, "—" for HORIZON
3. After 60s: "Backend unavailable" message appears
4. Confirmed by direct curl: `GET /api/research/factor-lab` → HTTP 500 every time
5. Confirmed compute_factor_lab works in a fresh Python shell (different memory context) — the issue is the live uvicorn process under memory pressure

**Expected:** Decile table with 10 rows, each showing numeric mean_return, plus rank-IC figure
**Actual:** "Backend unavailable" — HTTP 500 MemoryError on the unbounded ScannerResult.all() at research.py:216

---

### UT-05 — Factor Lab 10 decile rows with real figures
**Verdict:** FAIL
**Failure:** Same root cause as UT-04 — Factor Lab API returns 500, decile table never renders.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-04-fail.png`

**Expected:** 10 decile rows (Decile 1–10) with numeric mean_return; rank-IC figure visible
**Actual:** "Backend unavailable" — no decile table rendered

---

### UT-06 — Factor Lab N= drill-down is count-coherent
**Verdict:** FAIL
**Failure:** Factor Lab fails to load (same UT-04 root cause), so N= chips are never rendered and the drill-down cannot be tested.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-04-fail.png`

**Expected:** N= chip click → /research/samples total matches chip integer
**Actual:** N= chips never appear; Factor Lab shows "Backend unavailable"

---

### UT-15 — N= count coherence holds across multiple labs
**Verdict:** FAIL
**Failure:** Test requires coherence verification from both event-study AND factor-lab. Event-study portion passes (N=455 chip → 455 samples confirmed). Factor-lab portion cannot be tested — Factor Lab returns HTTP 500 (same MemoryError as UT-04), so factor-lab N= chips never appear.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-03-result.png`

**Expected:** N= coherence verified for both event-study and factor-lab chips
**Actual:** Event-study coherence PASS (N=455=455); factor-lab coherence BLOCKED by HTTP 500

---

### UT-19 — Five heavy labs load independently without interfering
**Verdict:** FAIL
**Failure:** Factor Lab consistently returns HTTP 500 (MemoryError), regardless of load order or isolation. The other 4 labs (event-study, regime-setup-pattern, downtrend-opportunity, factor-combination) all load successfully one-at-a-time. Factor Lab fails on every attempt.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/UT-04-fail.png`

**Expected:** All 5 labs load real data when visited one-at-a-time
**Actual:** 4/5 labs load successfully; Factor Lab shows "Backend unavailable" every time due to MemoryError at research.py:216

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Backend health:** `{"status":"ok","readiness":"ready","warmup":{"done":10,"total":10,"status":"ok"}}`
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-06-22
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-evidence/`
- **Backend log:** `/tmp/fanout-backend-8835.log`
- **System RAM available during testing:** ~10.5 GB (background test suite consuming memory)
- **ScannerResult rows in DB:** 609,166 (exceeds available memory for unbounded .all() load under concurrent pressure)
