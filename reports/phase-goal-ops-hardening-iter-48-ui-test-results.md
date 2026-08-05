# UI Test Results (merged)

**Date:** 2026-08-05
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 9/13 journeys passed (3 skipped, 1 required-missing, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-48-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-48-evidence/J-03-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-48-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-48-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-48-evidence/J-09-verify.png |
| UT-01 | `/data` loads without errors | smoke | P1 | Heading, job form (start/end/kind testids), readiness badge `ready`, no console errors | All present exactly as expected; `job-kind` defaulted to "Backfill snapshots"; `readiness-badge` `data-state="ready"` | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-01-result.png` |
| UT-02 | Historical-gap backfill reaches terminal status for its fixed step | happy-path | P1 | Running+spinner immediately; `aggregates-refreshed` mentions "membership timeline" within ~30s (must NOT take minutes); terminal status typically ~5 min, honest 20-min cap | Immediate running+spinner: yes. `aggregates-refreshed` within 30s: **no — never appeared** in 31+ min; API's `aggregates_refreshed` stayed `[]` the whole time. Terminal status: **never reached** within 31+ min (exceeds the disclosed 20-min cap). Independently corroborated by the dev's own isolated live TC-1 test FAILING identically. | FAIL | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-02-fail.png` |
| UT-03 | Backfilled date renders on Scanner Runs | happy-path | P1 | `2012-06-15` row + working run-detail page | Not tested — precondition (UT-02 job terminal) never met | SKIPPED | none |
| UT-04 | Job form blocks incomplete date range | validation | P2 | Start button disabled with empty start-date | Confirmed: `disabled: true` with start="" end="2012-06-16" | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-04-result.png` |
| UT-05 | Backend stays responsive during finalize tail | error | P1 | `readiness-badge` stays `ready`; page stays navigable | `readiness-badge` = `ready` at every check across a 31+ min observation window (5+ spot checks); `/data`⇄`/scanner-runs` navigation worked throughout; `GET /api/health` returned 200 on essentially every poll (one borderline 5s-timeout in my own tight external polling loop that recovered on the very next poll — consistent with the project's own documented "contention latency, not a code regression" finding for `/api/health` under concurrent Chrome-MCP load, `reports/perf-budgets.md` line 4261) | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-05-result.png` |
| UT-06 | Evidence drawdown-expectations panel still renders correctly | regression | P2 | Populated table, real figures, no `MemoryError`/500 | `evidence-claim-regime` badge "Regime: Risk-on" found; `evidence-expectations-table` rendered 5 populated `evidence-expectations-phase-row` rows with real percentage/day figures; `evidence-expectations-unavailable` NOT present | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-06-result.png` |
| UT-07 | Factor Lab decile drill-down still works | regression | P3 | Page loads, `N=` link opens samples drill-down | Page loaded ("Research — Factor Lab" heading rendered) but the first-read whole-dataset compute (`factors-table`) had not finished after 26+ min against a documented "a minute or two" norm — never reached a state where the decile grid / `N=` links existed to click | SKIPPED | none |
| UT-08 | Zero-work re-run reads honestly | ux | P2 | `no new snapshots` badge, `zero-work-note` panel, `0` new snapshots | Not tested — precondition (UT-02 job terminal) never met, and the test plan's own note bars starting a second job while one is still finishing | SKIPPED | none |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-04` — no test case executed for J-04 by any lane

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Failed Tests

### UT-02 — Historical-gap backfill reaches terminal status for its fixed step

**Verdict:** FAIL
**Failure:** Immediate running+spinner: yes. `aggregates-refreshed` within 30s: **no — never appeared** in 31+ min; API's `aggregates_refreshed` stayed `[]` the whole time. Terminal status: **never reached** within 31+ min (exceeds the disclosed 20-min cap). Independently corroborated by the dev's own isolated live TC-1 test FAILING identically.
**Evidence:** ``reports/qa/goal-ops-hardening-iter-48-evidence/UT-02-fail.png``

## Skipped Tests

### UT-03 — Backfilled date renders on Scanner Runs

**Verdict:** SKIPPED
**Reason:** Not tested — precondition (UT-02 job terminal) never met

### UT-07 — Factor Lab decile drill-down still works

**Verdict:** SKIPPED
**Reason:** Page loaded ("Research — Factor Lab" heading rendered) but the first-read whole-dataset compute (`factors-table`) had not finished after 26+ min against a documented "a minute or two" norm — never reached a state where the decile grid / `N=` links existed to click

### UT-08 — Zero-work re-run reads honestly

**Verdict:** SKIPPED
**Reason:** Not tested — precondition (UT-02 job terminal) never met, and the test plan's own note bars starting a second job while one is still finishing

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-05


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
