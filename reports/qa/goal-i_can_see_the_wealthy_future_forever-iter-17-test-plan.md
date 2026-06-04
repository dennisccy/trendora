# goal-i_can_see_the_wealthy_future_forever-iter-17 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

As-of-scope the forward-test evidence aggregate (forward return by A–E bucket, excess vs SPY/QQQ, by setup/regime, VCP/pattern breakdowns, control group) to an expanding window of every snapshot dated ≤ the global as-of date, relocate its single serving home from `GET /api/system-health` to `GET /api/backtest`, and retire `/system-health` entirely — all under the single global as-of switcher with no page-local date control.

## Test Cases

### TC-01 — As-of scoping restricts observation pool to runs ≤ D

**Type:** api (backend unit/integration — `apps/backend/tests/test_forward_testing.py`)
**Preconditions:** Fixture with multiple `ScannerRun.asof_date`s spanning at least 3 distinct dates, each with forward_returns rows.

**Steps:**
1. Call `compute_forward_aggregates(session, horizon, config, as_of=D)` for an early D and again for the latest D.
2. Inspect which runs/observations contributed to each result.
3. Compare top-level `n` (and per-group `n`) between early-D and latest-D results.

**Expected outcome:** Only runs with `asof_date <= D` contribute. `n` at an early D is strictly less than `n` at the latest D (sample non-decreasing toward latest).
**Pass criteria:** No contributing run has `asof_date > D`; `n(earlyD) < n(latestD)`.

---

### TC-02 — `as_of=None` byte-identical to all-history and equals latest-date case

**Type:** api (backend unit)
**Preconditions:** Same multi-date fixture as TC-01.

**Steps:**
1. Call `compute_forward_aggregates(..., as_of=None)`.
2. Call `compute_forward_aggregates(..., as_of=<latest asof_date in fixture>)`.
3. Deep-compare both result structures (top-level means/`n` and every per-group `n`/mean).

**Expected outcome:** The two results are identical; `as_of=None` preserves today's all-history behaviour unchanged.
**Pass criteria:** Structural equality (top-level + per-group `n` and means) between `as_of=None` and `as_of=latest`.

---

### TC-03 — No >D leak (a run strictly after D contributes zero)

**Type:** api (backend unit)
**Preconditions:** Fixture containing at least one run dated strictly after the chosen cutoff D.

**Steps:**
1. Call `compute_forward_aggregates(..., as_of=D)` where at least one run has `asof_date > D`.
2. Check every group (bucket A–E, setup, regime, VCP/pattern, control group) for any observation traceable to the post-D run.

**Expected outcome:** The post-D run contributes 0 observations to every group; no lookahead.
**Pass criteria:** Zero observations from any `asof_date > D` run appear in any group of the as-of-D aggregate.

---

### TC-04 — Relocated consistency invariant on as-of-scoped aggregate

**Type:** api (backend unit — moved from deleted System Health test, NOT a new test)
**Preconditions:** Multi-date fixture; the old `test_api_system_health.py` consistency test removed.

**Steps:**
1. Compute the as-of-scoped aggregate at a horizon.
2. Read `attribution.distribution.mean` and `overall.mean_return`.

**Expected outcome:** The distribution mean equals the overall mean for the as-of-scoped pool (the invariant binds the aggregate, not the per-date scorecard).
**Pass criteria:** `attribution.distribution.mean == overall.mean_return` (within float tolerance) on the as-of-scoped aggregate; test lives on the Backtest/aggregate path.

---

### TC-05 — Low-sample / empty cells show NA + n, never fabricated

**Type:** api (backend unit)
**Preconditions:** A cutoff date D with too few in-window snapshots; a bucket/setup/regime with no observations ≤ D.

**Steps:**
1. Call `compute_forward_aggregates(..., as_of=<early/sparse D>)`.
2. Inspect cells below `walk_forward.min_sample` and an empty regime/bucket.

**Expected outcome:** Cells below min_sample and empty groups report NA with the sample size `n` (`n=0` for empty), never a synthesized return.
**Pass criteria:** Sub-min_sample cells = NA with `n`; empty group = NA with `n=0`; no numeric return present where `n < min_sample` or `n=0`.

---

### TC-06 — `GET /api/backtest?as_of=D` returns `evidence_by_horizon`

**Type:** api
**Preconditions:** Backend running; a valid historical as-of date with snapshots.

**Steps:**
1. `curl -s "http://localhost:8000/api/backtest?as_of=<historical-date>"`
2. Inspect the JSON for `evidence_by_horizon` keyed by each `config.walk_forward.horizons` entry.
3. Verify each horizon entry carries the by-bucket A–E table, excess vs SPY/QQQ, by-setup, by-regime, VCP/pattern, and control-group fields.

**Expected outcome:** HTTP 200; payload includes `evidence_by_horizon` with one entry per configured horizon, each containing the full aggregate shape with `n`/NA.
**Pass criteria:** Status 200; `evidence_by_horizon` present with expected per-horizon keys and aggregate sub-fields; cutoff equals the resolved `run.asof_date` (no separate date param accepted).

---

### TC-07 — `GET /api/system-health` route is removed (404)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/system-health"`

**Expected outcome:** Route no longer registered.
**Pass criteria:** HTTP 404 (or route absent); no `system_health` router in `main.py`.

---

### TC-08 — Unknown / short horizon → NA, not fabricated; invalid as_of handled

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Request the aggregate for a horizon with insufficient forward data (short/unknown horizon).
2. `curl` `/api/backtest` with an invalid `as_of` value.

**Expected outcome:** Short/unknown horizon cells return NA + `n`; invalid `as_of` is rejected or defaulted exactly as today (no new error behaviour, no fabricated returns).
**Pass criteria:** No fabricated numbers for unsupported horizons; invalid `as_of` returns the same status/default as current behaviour.

---

### TC-09 — No `/system-health` references remain in `apps/` source

**Type:** artifact
**Preconditions:** Working tree after dev changes.

**Steps:**
1. `grep -rn "system-health\|system_health\|fetchSystemHealth\|SystemHealthResponse" apps/ --include=*.ts --include=*.tsx --include=*.py` (excluding `.next/` build artifacts).

**Expected outcome:** No dangling source references to the retired route, page, client, or type.
**Pass criteria:** Grep returns no hits in source files (`.next/` artifacts excluded); `system_health.py`, frontend `system-health/page.tsx`, and `fetchSystemHealth` are deleted.

---

### TC-10 — Full backend pytest green (run ONCE)

**Type:** artifact (test-suite execution)
**Preconditions:** Backend deps installed; run a single pytest invocation (~14 min; never two concurrent).

**Steps:**
1. Run the project test command once, capturing full output to the QA log.

**Expected outcome:** All backend tests pass, including new as-of-scoping/no-leak/relocated-invariant tests and the deleted System Health test no longer present.
**Pass criteria:** Exit code 0; no failures/errors; new TC-01..TC-08 backing tests present and green.

---

### TC-11 — Frontend typechecks / builds

**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. Run the frontend typecheck/build command.

**Expected outcome:** No TypeScript or build errors after removing System Health page/client and adding evidence panels.
**Pass criteria:** Typecheck/build exits 0.

---

### TC-12 — J-09: Backtest shows as-of-scoped evidence aggregate that re-points on as-of change

**Type:** browser (Chrome MCP — clean hydrated build per iter-15 lesson)
**Preconditions:** Stop `next dev` by port, `rm -rf apps/frontend/.next`, restart; confirm `GET /_next/static/chunks/main-app.js → 200` and health badge clears. Backend running.

**Steps:**
1. Navigate to `/backtest`; read the forward-return-by-bucket A–E table, excess vs SPY/QQQ, by-setup, by-regime — each showing `n`. Screenshot (save under `reports/qa/<phase>-evidence/TC-12-evidence-latest.png`).
2. Using **in-app nav/clicks** (not a hard reload), move the global as-of switcher to an earlier historical date.
3. Assert via distinct screenshot + DOM/network that the evidence re-points and `n` drops.
4. Return to the latest date; confirm the aggregate matches the full all-history figures.
5. Confirm the panel is labelled the expanding-window aggregate ("evidence from every snapshot dated ≤ D"), visually distinct from the per-date scorecard, and carries the survivorship-bias / universe-relative label.

**Expected outcome:** Evidence aggregate renders with `n`, re-points on global as-of change, `n` shrinks for earlier D, and returns to all-history at latest.
**Pass criteria:** Two **distinct** screenshots (de-duped by sha256) + a DOM/network assertion show different evidence and lower `n` for the earlier date; latest matches all-history; no `as_of` date param in page URL.

---

### TC-13 — J-10: Control-group comparison renders, numeric and labelled

**Type:** browser (Chrome MCP)
**Preconditions:** Same clean build as TC-12.

**Steps:**
1. On `/backtest`, locate the control-group comparison panel at a stated horizon.
2. Read the three arms: top-ranked cohort vs random-same-sector vs SPY/QQQ/sector ETF.

**Expected outcome:** Each control-group arm is numeric (or honest NA + `n`) and clearly labelled at a stated horizon.
**Pass criteria:** All three control-group arms present, labelled, with numeric values or NA+`n`; screenshot saved under evidence dir.

---

### TC-14 — J-18 (principal anti-goal): exactly one date selector on `/backtest`

**Type:** browser (Chrome MCP)
**Preconditions:** Same clean build.

**Steps:**
1. Inspect `/backtest` DOM for any page-local date dropdown/picker — confirm none exists.
2. Toggle the global as-of switcher; confirm BOTH the per-date scorecard AND the evidence aggregate re-point together.
3. Inspect the page URL — confirm it carries no date param.
4. Confirm the only date-bearing call is `/api/backtest?as_of=<global date>` (the single global date being read), and the horizon selector triggers **no** refetch (J-15).

**Expected outcome:** No second date state; one global switcher drives everything; URL date-free; horizon change is client-side only.
**Pass criteria:** No page-local date control in DOM; URL has no date param; single `?as_of=` call reflects the global date; horizon change does not issue a new fetch.

---

### TC-15 — Regression spot-checks on `/backtest` and global as-of

**Type:** browser (Chrome MCP)
**Preconditions:** Same clean build.

**Steps:**
1. On `/backtest` confirm: J-14 per-date scorecard renders alongside the aggregate; J-19 Return Attribution renders; J-21 leadership lists (Top Sectors / Themes / Ranked Cohort) appear **below** Return Attribution; J-16 VCP-vs-non-VCP and J-28 pattern breakdowns present.
2. Navigate to another page and confirm J-13 global as-of still re-points it.

**Expected outcome:** All required-still-passing journeys remain green; evidence panel placement respects J-21 ordering (bottom or top, never between scorecard/attribution/leadership lists).
**Pass criteria:** Scorecard + attribution + breakdowns render; leadership lists remain below attribution; global as-of re-points other pages; no regression observed.

---

## Summary

Total test cases: 15

- API tests: 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08)
- Browser tests: 4 (TC-12, TC-13, TC-14, TC-15)
- Artifact checks: 3 (TC-09, TC-10, TC-11)

**Critical-path coverage:** No-recompute / read-only grouping (TC-01, TC-06), No-lookahead / no >D leak (TC-03), Single-source consistency invariant relocated not deleted (TC-04), Exactly-one-date-selector J-18 (TC-14), No fabricated data / honest NA (TC-05, TC-08), System Health fully retired (TC-07, TC-09).
