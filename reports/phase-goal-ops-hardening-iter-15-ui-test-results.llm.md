# Phase goal-ops-hardening-iter-15 — UI Test Results

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 tests executed this session passed (0 failed, 0 skipped). All P1 tests pass.
3 additional required-still-passing journeys (J-01, J-03, J-05) are already verified `PASS` via
deterministic golden-script replay (`reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md`,
Test IDs `UT-J-01`/`UT-J-03`/`UT-J-05`) — per this run's explicit dispatch instructions they were
NOT re-tested and NO competing row is emitted for them here; those rows merge into the combined
results separately. See "Required-still-passing journeys not independently re-executed" below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/backtest` loads against the warm cache | smoke | P1 | Page renders (no blank/error overlay, no "Backend unavailable" card); `evidence-aggregate` present, not stuck on skeleton; `backtest-asof` badge shows real "Viewing as-of" text; scorecard table shows all 5 horizons (1d/5d/10d/20d/60d), each populated with figures or the honest "—" (NA) placeholder; resolves within ~10s given warm cache; no console errors | Navigated to `/backtest`; rendered immediately. `evidence-aggregate` testid present=true; "Backend unavailable" text absent; `backtest-asof`="Viewing as-of 2026-07-22 (latest)"; all 5 horizon rows (1d/5d/10d/20d/60d) present, each showing the honest "—n=0 ⚠" NA placeholder with the page's own explanatory caption ("No elapsed forward window for this date yet... every horizon is NA (n=0)... No numbers are fabricated") — correct for the latest as-of date, not a broken/blank row; forward-tested evidence aggregate section at the bottom fully populated (e.g. bucket A +10.72% n=8787). Resource Timing API showed 2 `GET /api/backtest` calls at 116.9ms and 554.1ms — both far under the 1.5s budget (warm cache-HIT path). Console: 1 informational React DevTools line, zero red errors | PASS | `reports/qa/goal-ops-hardening-iter-15-evidence/UT-01-result.png` |
| UT-02 | Two simultaneous tabs on the same warm `/backtest` date show identical numbers | regression | P2 | Both tabs' `backtest-asof` name the same date; both resolve within a few seconds, neither hangs or shows "Backend unavailable"; the two tabs' row-text arrays are character-for-character identical | Opened a second Chrome tab to the same `/backtest` URL while the first stayed open. Both tabs' `backtest-asof`="Viewing as-of 2026-07-22 (latest)". Captured `Array.from(document.querySelectorAll("table tbody tr")).map(r=>r.textContent)` in both tabs (49 rows spanning the scorecard, ranked-cohort, and evidence-aggregate tables) — JSON output byte-for-byte identical between tabs. Neither tab showed "Backend unavailable"; `evidence-aggregate` present in both | PASS | `reports/qa/goal-ops-hardening-iter-15-evidence/UT-02-tab2-result.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (test-plan `UT-05`) | regression | P1 | Boot ≤5s; boot-phase visible pre-ready; crash → explicit unreachable state; log truncates on crash; mid-flight job shows interrupted state on restart (steps + Acceptance per `docs/goal.md`) | This iteration's diff touches none of J-04's code (`app.engine.readiness`, `app/api/health.py`, boot sequence — confirmed unchanged via `git status` and the ui-surface-map's "Backend-Only Changes" section). Per `UT-05`'s own precondition text ("Carrying forward is the preferred path this iteration") and this dispatch's pump note ("the preferred option per the plan is CARRYING iter-14's already-closed live pass"; services must not be killed/restarted this session), carried iter-14's dedicated same-day crash/restart pass forward rather than re-inducing a live kill: real operator-scheduled kill (12:57:13 BST)+restart (13:01:13 BST) closed all 6 steps end-to-end — badge/banner flipped to "Backend unavailable"/NO-GO immediately on kill (no frozen "Ready", no blank page); badge showed "Initializing… history 89/89" pre-ready, settling to "Ready" via the same open tab's own live polling; `logs/backend.log` truncated abruptly at the kill (no clean-shutdown entry) vs. 5 other same-day PIDs; `/data`'s Run History row for the killed job showed `run-status`="interrupted" (neutral badge) with frozen non-zero progress; boot-to-first-200 measured 1.80s (`reports/perf-budgets.md`), well under the 5s budget. This session's OWN fresh re-check today: `GET /api/health` → `readiness`="ready", `preflight.verdict`="GO"; homepage AND `/data`'s `readiness-badge` both `data-state`="ready" text "Ready"; `/data`'s Run History table renders populated — no regression in the steady-state path this iteration's fix could plausibly have touched. No live crash/restart was performed by this session (no operator channel available; the plan explicitly prefers carry-forward here since nothing in J-04's own code changed) | PASS (carried forward from iter-14 + this session's steady-state sanity re-check) | `reports/qa/goal-ops-hardening-iter-15-evidence/UT-J-04-carryforward-sanity.png`; carried evidence: `reports/phase-goal-ops-hardening-iter-14-ui-test-results.llm.md` ("J-04 Follow-Up" section, screenshots `UT-J-04-01..06*.png`) |
| UT-07 | Nothing new to discover: the product looks and navigates exactly as before | ux | P3 | No new nav entry/page/button/label anywhere; `/backtest`'s section order matches iter-14's documented structure exactly | Home-page nav list (11 entries): Dashboard(`/`), Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager(`/data`) — exact match, nothing added/removed. `/backtest`'s h2/h3 order: "As-of scan summary" → "Forward-test scorecard" → "Return attribution" (+ 4 subsections) → "Leadership cohorts" (+ "Ranked cohort") → "Forward-tested evidence (expanding window…)" at the bottom (+ 9 subsections) — exact match to iter-14's documented order | PASS | `reports/qa/goal-ops-hardening-iter-15-evidence/UT-07-nav-result.png`, `reports/qa/goal-ops-hardening-iter-15-evidence/UT-07-backtest-sections.png` |

---

## Passed Tests

### UT-01 — `/backtest` loads against the warm cache
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-15-evidence/UT-01-result.png`
- Page rendered fully on first navigation with the cache warm (per PUMP NOTE, backend was not restarted). No "Backend unavailable" card, no Next.js error overlay. `evidence-aggregate` present and populated (not stuck on `BacktestSkeleton`). Both observed `GET /api/backtest` calls resolved in 116.9ms / 554.1ms via the Resource Timing API — comfortably inside the ≤1.5s budget, confirming the warm/cache-HIT path is unaffected by this iteration's de-dup fix. Zero console errors.

### UT-02 — Two simultaneous tabs on the same warm `/backtest` date show identical numbers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-15-evidence/UT-02-tab2-result.png`
- Opened a second tab onto the same `/backtest` URL while the first remained open (both landed on the same latest as-of, 2026-07-22, since the as-of switcher is global). Captured each tab's full `table tbody tr` text array (49 rows) via `eval` — the two arrays were character-for-character identical, and both tabs' `backtest-asof` badges named the same date. No evidence of the new lock/in-flight-dictionary code corrupting or staggering the ordinary cache-HIT path.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** PASS (carried forward + this session's sanity re-check)
**Evidence:** `reports/qa/goal-ops-hardening-iter-15-evidence/UT-J-04-carryforward-sanity.png`; carried: `reports/phase-goal-ops-hardening-iter-14-ui-test-results.llm.md`
- This iteration's diff is confirmed scoped to `apps/backend/app/engine/forward_testing.py` and its test file only (per `git status` and the ui-surface-map) — none of J-04's own surfaces (`app.engine.readiness`, `app/api/health.py`, the boot sequence, `PreflightBanner`/`HealthBadge`) were touched. Per the test-plan's own stated preference and this dispatch's pump note, iter-14's same-day dedicated crash/restart pass (12:53–13:11 BST) is carried forward as the evidence for J-04's 6 steps, rather than re-inducing a live kill this session (not possible this turn — no operator channel, services must stay up). This session independently re-confirmed the steady-state ready path still holds: `GET /api/health` reports `readiness`="ready" / `preflight.verdict`="GO"; the homepage and `/data` page's `readiness-badge` both read `data-state="ready"`; `/data`'s Run History table renders populated with no visible corruption.

### UT-07 — Nothing new to discover: the product looks and navigates exactly as before
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-15-evidence/UT-07-nav-result.png`, `reports/qa/goal-ops-hardening-iter-15-evidence/UT-07-backtest-sections.png`
- Nav sidebar lists exactly the 11 expected entries, nothing new. `/backtest`'s heading order matches iter-14's documented structure exactly, confirming this iteration's fix has zero visible UI footprint, as its own user-visible-changes report claims.

---

## Failed Tests

None this run.

---

## Skipped Tests

None this run.

---

## Required-still-passing journeys not independently re-executed (per dispatch instruction)

Per this run's explicit "GOAL-MODE REGRESSION LANES" dispatch instructions, the following
Required-still-passing journeys were **not** re-tested and **no row is emitted for them in the
table above** — their `PASS` rows come from the deterministic golden-script replay lane and merge
into the combined results separately:

| Journey | Test-plan case (this file's own numbering) | Where its PASS evidence lives |
|---|---|---|
| J-01 — Backfill honors the requested range and explains zero-work | UT-03 | `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md`, Test ID `UT-J-01` = PASS |
| J-03 — No per-run range cap | UT-04 | same file, Test ID `UT-J-03` = PASS |
| J-05 — Aggregates are precomputed at ingest, never on the fly | UT-06 | same file, Test ID `UT-J-05` = PASS |

I confirmed directly (by reading the file) that all three rows read `PASS` before deciding not to
perform the UT-03/UT-04/UT-06 manual walkthroughs, consistent with each case's own Step 1 instruction
("If the report is missing this row or shows anything other than PASS, perform the manual/LLM-fallback
walkthrough below").

## Golden replay scripts

No new/updated golden replay script was written this run. `UT-01`/`UT-02`/`UT-07` are iter-15-local
test-plan cases, not `docs/goal.md` Must-have journeys, so they are out of scope for the golden-script
mechanism. `J-04` (this run's one in-scope journey) was not re-verified via a fresh live browser
walkthrough this turn (carried forward per above) and, independent of that, its steps require an actual
backend process kill/restart that the replay schema's three action types (`goto`/`click`/`fill`) cannot
express — consistent with iter-14's own established conclusion that J-04 cannot be replayed
deterministically by `demo_runner.py`. `runs/goal-session-ops-hardening/journey-scripts/J-04.json` was
therefore not created, and the existing `J-01.json`/`J-03.json`/`J-05.json` were left untouched (not
re-verified by this session).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (persistent Chrome/CDP session)
- **Test Date:** 2026-07-23
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-15-evidence/`
- **Backend health at test time:** `GET /api/health` → `status`="ok", `db_ok`=true, `readiness`="ready", `preflight.verdict`="GO", `seed_latest_date`="2026-07-22", `symbol_count`=591
