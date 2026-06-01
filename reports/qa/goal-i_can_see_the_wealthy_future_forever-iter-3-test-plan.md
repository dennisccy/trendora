# goal-i_can_see_the_wealthy_future_forever-iter-3 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3
**Date:** 2026-06-01
**Frontend Present:** yes

## Phase Goal

Ship the **Data Manager** (`/data`): a user views dataset coverage/gaps, starts an async fetch+backfill job over a date/range, watches live progress and a final summary, and afterward finds new as-of dates selectable in the global switcher and System Health `n` grown — all real-data-only, immutable, lookahead-free, reusing the canonical `scanner.run_scan` + `forward_testing.backfill_run_forward_returns` paths (no second computation).

## Test Cases

### TC-01 — Coverage endpoint reports true dataset metadata

**Type:** api
**Preconditions:** Backend running on `:8000` with the committed seed (1356 bars/symbol, 158 symbols, quarterly bootstrap snapshots).

**Steps:**
1. `curl -s http://localhost:8000/api/data | jq .`

**Expected outcome:** Returns coverage (price-history min/max date, symbol count, sorted snapshot/as-of date set, gaps = trading days with bars but no snapshot) plus recent `DataProviderRun` run history.
**Pass criteria:** HTTP 200; `coverage.symbol_count == 158`; price range min ≈ `2021-01-04`, max ≈ `2026-05-28`; `gaps` is a non-empty list of date strings; `runs`/history array present. Values descriptive only — not recomputed scores.

---

### TC-02 — Coverage correctness on fixture (unit)

**Type:** artifact
**Preconditions:** `apps/backend/tests/test_data_manager.py` exists.

**Steps:**
1. Confirm a test asserts `compute_coverage(session, cfg)` returns correct price-range, symbol-count, snapshot-date set, and gaps on a small fixture.

**Expected outcome:** Test present and passing.
**Pass criteria:** Test exists, maps to `compute_coverage`, and passes in the suite run (TC-15).

---

### TC-03 — Start backfill job returns job_id immediately

**Type:** api
**Preconditions:** Backend running; pick a date range of older seed-bar trading days with bars but no snapshot (a gap range from TC-01).

**Steps:**
1. `curl -s -X POST http://localhost:8000/api/data/jobs -H 'Content-Type: application/json' -d '{"kind":"backfill","start":"<gap_start>","end":"<gap_end>"}'`

**Expected outcome:** Returns `{ "job_id": "..." }` without blocking on job completion.
**Pass criteria:** HTTP 200/202; response contains a non-empty `job_id`; response returns promptly (does not wait for full backfill).

---

### TC-04 — Job status polling reports progress then final summary

**Type:** api
**Preconditions:** TC-03 returned a `job_id`.

**Steps:**
1. Poll `curl -s http://localhost:8000/api/data/jobs/<job_id>` repeatedly until status is terminal.

**Expected outcome:** Status transitions from running (with progress e.g. `snapshots a/b dates`, `fetched x/y symbols`) to a final success/partial/failure summary with ok-vs-failed counts.
**Pass criteria:** At least one in-progress response shows advancing counts; final response shows terminal status (`success`/`partial`/`failed`) with `dates_done/total` and `symbols_ok`/`symbols_failed`.

---

### TC-05 — Invalid job ranges rejected with explicit 4xx

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `POST /api/data/jobs` with `start > end`.
2. `POST /api/data/jobs` with empty/missing range.
3. `POST /api/data/jobs` with a malformed date (e.g. `"2026-13-99"`).

**Expected outcome:** Each rejected with an explicit 4xx and error message — no silent no-op job created.
**Pass criteria:** All three return HTTP 4xx; no `job_id` issued; error body explains the rejection.

---

### TC-06 — Backfill grows n deterministically (unit)

**Type:** artifact
**Preconditions:** `tests/test_data_manager.py`.

**Steps:**
1. Confirm a test backfills a range of older seed-bar dates and asserts `compute_forward_aggregates(...).n` increases (`n_after > n_before`) and the expected `ScannerRun` rows are added.

**Expected outcome:** Test present and passing.
**Pass criteria:** Test exists and passes (TC-15).

---

### TC-07 — Backfill is lookahead-free (unit)

**Type:** artifact
**Preconditions:** `tests/test_data_manager.py`.

**Steps:**
1. Confirm a test asserts a range-backfilled snapshot for date D equals a direct `scanner.run_scan(D)`, uses only bars ≤ D, and forward returns use only bars > D.

**Expected outcome:** Test present and passing.
**Pass criteria:** Test exists, asserts ≤ D scoring and > D forward returns, and passes (TC-15).

---

### TC-08 — Create-once / immutable backfill (unit)

**Type:** artifact
**Preconditions:** `tests/test_data_manager.py`.

**Steps:**
1. Confirm a test asserts backfilling a date that already has a snapshot is a no-op (same row id, unchanged `created_at`, result rows unchanged), re-running the same range twice yields identical content, and `DataProviderRun` stays append-only.

**Expected outcome:** Test present and passing.
**Pass criteria:** Test exists and passes (TC-15).

---

### TC-09 — No second scan/return computation path (artifact / coherence)

**Type:** artifact
**Preconditions:** `apps/backend/app/engine/data_manager.py` exists.

**Steps:**
1. Inspect `data_manager.py`: confirm `run_data_job` calls `scanner.run_scan` (via/with `get_run_for_date`) and `forward_testing.backfill_run_forward_returns`.
2. Confirm there is **no** new scoring/forward-return math inside `data_manager.py`.

**Expected outcome:** Backfill orchestrates existing canonical modules only.
**Pass criteria:** Both canonical calls present; no reimplemented score/return computation. Any new scan/return math = FAIL.

---

### TC-10 — Forced live-fetch failure: explicit error, zero fabricated data (unit)

**Type:** artifact
**Preconditions:** `tests/test_stooq_provider.py` (and/or job test) exists.

**Steps:**
1. Confirm a test stubs the live/`stooq` provider to raise `ProviderUnavailableError` and asserts the job ends failed/partial with an explicit message.
2. Confirm it asserts **zero** fabricated `DailyPrice` rows and **zero** snapshots written for the failed symbols.

**Expected outcome:** Failure surfaced honestly; no synthesized prices/scores.
**Pass criteria:** Test exists and passes (TC-15); asserts both the explicit error and zero-write behavior.

---

### TC-11 — Live Stooq real-provider integration test (documented skip allowed)

**Type:** artifact
**Preconditions:** `tests/test_stooq_provider.py`.

**Steps:**
1. Confirm one `@pytest.mark.integration` test hits real Stooq for a single symbol.
2. Confirm the dev handoff states explicitly whether it ran against the real provider or only the forced-failure stub.

**Expected outcome:** Integration test present; honest documentation of run/skip.
**Pass criteria:** Marked test exists; handoff (`docs/handoffs/...-iter-3-dev.md`) states real-fetch result or documented offline skip — never a silent pass.

---

### TC-12 — Config-driven tunables / no magic numbers (unit)

**Type:** artifact
**Preconditions:** `config.yaml` `data_manager` block + `DataManagerCfg`; `test_no_magic_numbers` (or equivalent).

**Steps:**
1. Confirm every `data_manager` tunable (e.g. `live_provider`, `max_range_days`, job limits) is read from config, not hard-coded.
2. Confirm `test_no_magic_numbers` (or equivalent) stays green.

**Expected outcome:** No magic numbers in calc/control code.
**Pass criteria:** Config block present; tunables read from config; magic-number test passes (TC-15).

---

### TC-13 — `/data` date inputs are job parameters, not a second as-of state (artifact)

**Type:** artifact
**Preconditions:** `apps/frontend/app/data/page.tsx` exists.

**Steps:**
1. Inspect `app/data/page.tsx`: confirm the date/range inputs are local job parameters.
2. Confirm they do **not** call/bind `useAsOf` / `setAsOf` or create a second global viewing date state.

**Expected outcome:** "Exactly one date selector" (J-18) preserved; `/data` inputs select what to fetch/backfill only.
**Pass criteria:** No binding of `/data` date inputs to the global as-of provider; J-18 viewing control untouched.

---

### TC-14 — Sidebar nav entry + as-of `refresh()` additive (artifact)

**Type:** artifact
**Preconditions:** `components/sidebar.tsx`, `components/asof-provider.tsx`.

**Steps:**
1. Confirm `sidebar.tsx` `NAV` includes `{ href: "/data", label: "Data Manager", icon: Database }`.
2. Confirm `asof-provider.tsx` exposes an additive `refresh()` that re-fetches `/api/runs` and preserves the current `asOf` (and leaves `latest` unchanged for older-date backfills).

**Expected outcome:** Nav entry present; non-disruptive `refresh()` available.
**Pass criteria:** Both present; `refresh()` only adds date options, does not reset the user's selection.

---

### TC-15 — Backend test suite passes (no regressions)

**Type:** artifact
**Preconditions:** Backend test command from `.claude/project-template.md`. (Full pytest ~14 min — run once, not concurrently.)

**Steps:**
1. Run the full backend test suite, capturing output to `reports/qa/<phase>-test.log`.

**Expected outcome:** All tests pass including the new `test_data_manager.py`, `test_api_data.py`, `test_stooq_provider.py`, and updated config tests.
**Pass criteria:** Exit code 0; pass count ≥ iter-2 baseline of 266 plus the new tests; 0 failures, 0 regressions. (Documented integration skip for TC-11 is acceptable.)

---

### TC-16 — J-17 full multi-step flow (browser, PRIMARY)

**Type:** browser
**Preconditions:** Backend `:8000` and frontend `:3000` running.

**Steps:**
1. Navigate to `http://localhost:3000/data`; verify Coverage panel renders (price range, symbol count, snapshot/as-of dates, gaps).
2. In the Job form, pick a backfill date range over offline seed-bar gap dates; click **Start**.
3. Observe the live-progress panel advance (`snapshots a/b dates`, `fetched x/y symbols`).
4. Read the final summary (ok vs failed counts, terminal status).
5. Open the global as-of switcher (no hard reload) and confirm a previously-absent backfilled date is now selectable; select it and confirm it resolves on `/stocks` and `/`.
6. Navigate to `/system-health`; confirm sample size `n` is higher than before the job.

**Expected outcome:** Coverage → start → live progress → summary → new date selectable via `refresh()` (no reload) → `n` grew.
**Pass criteria:** Every step verified with screenshots in `reports/qa/<phase>-evidence/`; new date appears without a hard reload; `/system-health` n strictly increased. Screenshot at the start to capture pre-job `n`.

---

### TC-17 — Forced provider failure surfaced in UI (browser)

**Type:** browser
**Preconditions:** Frontend/backend running; live/fetch provider stubbed to fail (forced-failure path).

**Steps:**
1. On `/data`, start a **fetch** job that triggers the forced provider failure.
2. Observe the live-progress / summary panels.

**Expected outcome:** An explicit error state (error card + failed counts) appears — never a fake success; run summary records failed status.
**Pass criteria:** UI shows explicit error styling per design system; no fabricated success; failed counts shown. (May be SKIPPED if frontend not running — record reason.)

---

### TC-18 — Regression: required-still-passing journeys (browser)

**Type:** browser
**Preconditions:** Frontend/backend running; a backfilled date available from TC-16.

**Steps:**
1. **J-13:** global as-of switcher still changes the viewed date across pages (via in-app nav, not reload).
2. **J-14:** a backfilled date yields a valid per-date scorecard.
3. **J-08:** run list shows the new immutable runs.
4. **J-07:** a backfilled Risk-Off date still marks zero Actionable.
5. **J-09:** aggregate stays coherent.

**Expected outcome:** J-07, J-08, J-09, J-13, J-14 remain green; no regression.
**Pass criteria:** Each verified with evidence; no broken behavior. (May be SKIPPED if frontend not running — record reason; do not FAIL solely for skipped browser checks.)

---

### TC-19 — Default boot path unchanged (artifact)

**Type:** artifact
**Preconditions:** `apps/backend/main.py`.

**Steps:**
1. Confirm `main.py` lifespan still bootstraps quarterly seed snapshots + `backfill_forward_returns`, with `provider: seed`.
2. Confirm the only `main.py` change is `app.include_router(data.router, prefix="/api")` — live fetch is NOT in the boot path.

**Expected outcome:** Deterministic offline seed boot preserved; Data Manager is on-demand and additive.
**Pass criteria:** Lifespan boot untouched; router include is additive; no live fetch in boot.

---

## Summary

Total test cases: 19
- API tests: 4 (TC-01, TC-03, TC-04, TC-05)
- Browser tests: 3 (TC-16, TC-17, TC-18 — TC-16 is the primary J-17 flow)
- Artifact checks: 12 (TC-02, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-19)

> Note: TC-15 is the full backend suite gate. Critical anti-goal coverage: real-data-only (TC-10, TC-11, TC-17), immutable/lookahead-free backfill (TC-07, TC-08), no fabricated data (TC-10, TC-17), no second computation path (TC-09), exactly one date selector (TC-13), default boot unchanged (TC-19).
