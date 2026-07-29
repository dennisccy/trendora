# Phase goal-ops-hardening-iter-31 — UI Test Results

**Phase:** goal-ops-hardening-iter-31
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 tests passed (0 skipped)

---

## Scope note

`reports/phase-goal-ops-hardening-iter-31-ui-test-plan.md` and the UI surface map are both
marked N/A ("backend-only phase, Frontend Present: no") because no frontend files changed.
However the phase spec's own Definition of Done and Testing Requirements explicitly assign a
real-browser check to browser-qa-agent: `/research/factor-lab?all=true` opened in a real
browser must return HTTP 200 with real numeric values and zero console errors (this is the page
that previously crashed with `MemoryError` at `research.py:583` in iter-29/iter-30), and the
spec states this Factor-Lab spot-check IS this iteration's browser coverage for both target
journeys J-06 and J-07 ("Browser: J-06, J-07 (via the Factor Lab spot-check below, plus the
required-still-passing set's standard replay)"). This report executes that spot-check plus the
two ride-along, capture-only replay tasks the spec names (TC-9 for J-06, and the equivalent for
J-07). Required-still-passing journeys J-01/J-03/J-04/J-05/J-08/J-09 were already re-verified by
the pipeline's own deterministic-replay boot step before this agent was dispatched
(`reports/phase-goal-ops-hardening-iter-31-regression-replay-results.md`, 6/6 PASS) — per the
dispatch instructions those rows are excluded here and merge in automatically.

## MemoryError log-window citation (QA evidence-quality requirement)

- **THIS run's boot banner:** `logs/backend.log:132546` (`Uvicorn running on http://0.0.0.0:8255`),
  with `Started server process [194211]` at line 132543. Confirmed live: `ps aux` shows PID
  194211 as the currently running `uvicorn ... --port 8255` process — this boot banner belongs
  to the backend actually serving this test run, not a stale prior restart.
- **Window checked:** `logs/backend.log` lines 132546 through EOF (line 132809 at the time of
  the final check, after all requests below completed).
- **Result:** `grep -c "MemoryError" <(tail -n +132546 logs/backend.log)` = **0**. No
  `research.py` frame, no MemoryError, anywhere in this run's window. (Older MemoryError lines
  exist earlier in the same file, e.g. lines 129310/130038/130048/130094/132302 — all from prior
  process restarts before line 132543, i.e. historical evidence of the pre-fix bug, not this
  run.)

## Host-idle confirmation (DoD: "opened in a real browser on a verifiably idle host")

`GET /api/health` at test time: `background_compute.active: []` (a prior background compute for
`asof_key 2026-07-21` had completed at `2026-07-29T05:05:47Z`, ~20s before the browser test
began), `readiness: "ready"`, `warmup: 89/89`. `uptime` load average 0.75/1.00/0.99. Host was
idle, not mid-backfill, when the browser check ran.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-FL-01 | Factor Lab all-factors view loads without MemoryError | smoke | P1 | `/research/factor-lab` returns HTTP 200; decile table + rank-IC render real numeric values for every catalog factor at every configured horizon; zero console errors; zero MemoryError in backend log | Page loaded via real browser navigation; extracted page text shows all 11 catalog factors each with real rank-IC, N=771129 (or the factor's own real N), risk-adjusted, and FWD/MDD values populated for all 5 horizons (1d/5d/10d/20d/60d); console capture showed only a React-DevTools info line, zero errors; backend log shows 0 MemoryError since this run's boot banner (line 132546) | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png |
| UT-J-06 | Pages load only what they need (Factor Lab, this iteration's affected page) | regression | P1 | The one `/research` lab page in J-06's golden loads correctly (page-load smoke, per spec's Factor-Lab-spot-check mapping for this iteration); the previously-crashing Factor Lab page also loads | Golden script `J-06.json` replayed end-to-end via deterministic replay lane (demo_runner.py --mode verify), all 11 steps' expects held; supplemented by this agent's own live navigation to `/research/factor-lab` (the page this iteration's fix targets), which rendered correctly per UT-FL-01 | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-06-verify.png (ride-along replay) + reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png (live navigation) |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Per spec's mapping, this iteration's J-07 browser coverage is the Factor-Lab spot-check (AG-8 crash-avoidance) plus the golden's existing smoke check | Golden script `J-07.json` replayed end-to-end via deterministic replay lane, both steps' expects held (`/evidence` shows "-7.48%", `/data` shows "drawdown expectations"); backend stayed responsive throughout (health checks above) | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-07-verify.png |

---

## Passed Tests

### UT-FL-01 — Factor Lab all-factors view loads without MemoryError
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png` (fresh capture this run — md5 `9002cdee0d9019799029140f2a3cc3d1`, verified distinct from every prior `*factor-lab*.png` capture on disk across all iterations, no collision)

- Navigated Chrome MCP directly to `http://localhost:3255/research/factor-lab` (the page fires its own `?all=true` fetch on load, confirmed in `apps/frontend/app/research/_labs.tsx`).
- Extracted page text: heading "Research — Factor Lab", "Factors: 11", "Horizons: 1d · 5d · 10d · 20d · 60d", and a fully populated decile-evidence table — every one of the 11 catalog factors (Volatility, ATR %, Historical volatility, Risk score, Up/down volume, Volatility contraction, Relative strength vs SPY (3m), Leadership score, Entry Quality score, Moving-average stack, Proximity to 52-week high) shows real rank-IC (e.g. `+0.10`, `-0.07`), real N (`771129`, or `765882`/`769840` for the two factors with slightly fewer valid observations), real risk-adjusted values, and real FWD/MDD percentages for every one of the 5 horizons (1d/5d/10d/20d/60d) — e.g. Volatility: FWD 1D `+0.34%` … FWD 60D `+13.67%`, MDD 1D `-4.87%` … MDD 60D `-21.85%`.
- No "Backend unavailable" error box, no blank/frozen frame — the exact failure mode the iteration's fix targets was absent.
- Cross-checked the rendered table against the raw API payload (`GET /api/research/factor-lab?all=true`, fetched independently via curl): same 11-factor `factors_table`, same `n_total: 771129` for `leadership_score` — the browser is genuinely rendering the live engine output, not a stale/cached frame from a different run.
- Console: `enable_console_logging` was active before navigation; `get_console_messages` after page load returned exactly one line, an informational React DevTools notice (`Download the React DevTools...`) — zero warnings, zero errors. A sanity check (manually firing `console.error('qa-sanity-check-marker')` via `eval` on this same tab) confirmed the capture mechanism does record errors when they occur, so the absence of any app error is a genuine negative result, not a broken logging pipe.
- Repeat/concurrent-load spot-check (DoD item 2): fired 2 simultaneous `curl` requests at `GET /api/research/factor-lab?all=true` after the browser load; both returned `HTTP 200` in <30ms. Backend log confirms 5 total `GET /api/research/factor-lab?all=true` requests logged in this run's window, all `200 OK`, zero `404`/`500`/traceback lines except one unrelated `GET /research/factor-lab?all=true` (no `/api` prefix) returning `404` — a benign frontend-side stray request to a path that was never a backend route, not something this iteration changed, and it did not affect the page's actual render (the `/api/...` request that matters succeeded).
- Note: the cache was already warm going into this test (first `curl` probe returned in 0.054s, not a fresh cold-MISS compute), so this check does not itself exercise the cold-MISS/single-flight code path — that is proven separately by the unit tests named in the phase's IN SCOPE/DEFINITION OF DONE (`test_factor_lab_all.py`), which is out of this agent's remit to re-verify.

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-31-evidence/J-06-verify.png`
- Ran the existing golden `runs/goal-session-ops-hardening/journey-scripts/J-06.json` through the deterministic replay lane (`demo_runner.py --mode verify --journeys J-06`): `1 journey(s), 0 failed (verdict: PASS)`. All 11 steps' text expects held (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`).
- This closes the ride-along TC-9 gap named in the phase's NOTES/OUT OF SCOPE ("no artifact has existed for this row since iter-28") — a discoverable PASS result now exists at `reports/phase-goal-ops-hardening-iter-31-j06-ridealong-replay-results.md`. Per the spec this is capture-only and non-blocking, not this iteration's own goal (rule 7); the full real-browser 11-page TTI sweep J-06 step 1 still needs remains undone and carried forward, unchanged.
- Supplemented with this agent's own live navigation to `/research/factor-lab` (the specific `/research` lab this iteration's fix concerns) — see UT-FL-01.

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-31-evidence/J-07-verify.png`
- Ran the existing golden `runs/goal-session-ops-hardening/journey-scripts/J-07.json` through the deterministic replay lane: `1 journey(s), 0 failed (verdict: PASS)`. Both steps' text expects held (`/evidence` → "-7.48%", `/data` → "drawdown expectations").
- Per the phase's TESTING REQUIREMENTS, this iteration's browser coverage for J-07 is this golden replay plus the Factor-Lab spot-check (UT-FL-01), which is the AG-8 crash-avoidance property J-07's acceptance criteria care about. The full forward-aggregate-warm + continuous `/api/health` poll + memory-pressure-abort drill (J-07 steps 1/2/4) is not this iteration's own scope (it was covered structurally by prior iterations and is not re-exercised here).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), plus Chromium via Playwright for the two deterministic ride-along replays (`demo_runner.py --mode verify`)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-31-evidence/`
- **Backend log window cited:** `logs/backend.log` lines 132546–132809 (this run's boot banner through end of test window), 0 MemoryError lines
