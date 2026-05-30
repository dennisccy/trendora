# goal-i_can_see_the_wealthy_future-iter-5 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Frontend Present:** yes

## Phase Goal

Add the append-only **immutable scanner-snapshot spine**: persist dated `scanner_run` snapshots
(computed by calling the existing canonical engine once per as-of date, never recomputed), serve
them via new `/api/runs` + `/api/runs/{run_id}` endpoints, and graduate `/scanner-runs` and
`/scanner-runs/[runId]` from stubs to real pages — so a user can browse the history, open a seeded
**Risk-Off** run with **zero Actionable** stocks (J-07), and confirm an older run's rankings differ
from the latest (J-08), with J-01–J-06 unregressed.

## Test Cases

### TC-01 — `GET /api/runs` lists ≥2 dated runs, descending by as-of date
**Type:** api
**Preconditions:** Backend up at `:8000`; lifespan `bootstrap_runs` has persisted the bootstrap dates + latest seed date.

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8000/api/runs`

**Expected outcome:** `200`; JSON array of ≥2 runs, each with `run_id`, `asof_date`, `created_at`, `regime:{label,score}`, `candidate_counts`, `n_stocks`; ordered strictly descending by `asof_date`.
**Pass criteria:** Status `200`; length ≥2; `asof_date` values are sorted descending; ≥1 run has `regime.label == "Risk-off"`; each item has all listed fields.

### TC-02 — `GET /api/runs/{run_id}` returns one run's full stored snapshot
**Type:** api
**Preconditions:** A valid `run_id` obtained from TC-01.

**Steps:**
1. Capture a `run_id` from `/api/runs`.
2. `curl -s -w "\n%{http_code}" http://localhost:8000/api/runs/<run_id>`

**Expected outcome:** `200`; payload contains the run's regime panel (label + score + components), breadth (universe-relative), candidate counts, and a ranked stored stock-results array in the `StockRow` shape (ticker, leadership/entry-quality/risk score+bucket, setup_status, reason, rank).
**Pass criteria:** Status `200`; `asof_date` matches the selected run; stock-results array non-empty and ordered by `rank`; each row carries the three score blocks + bucket + `setup_status`.

### TC-03 — Risk-Off run stores `Risk-off` regime and ZERO Actionable (J-07 at API level)
**Type:** api
**Preconditions:** Bootstrap persisted a configured `"Risk-off"` date (e.g. 2025-04-04 or 2022-10-07).

**Steps:**
1. From `/api/runs`, find the run whose `regime.label == "Risk-off"`; capture its `run_id`.
2. `curl -s http://localhost:8000/api/runs/<run_id>`
3. Inspect every stock row's `setup_status`.

**Expected outcome:** Regime label is exactly `"Risk-off"`; **no** stock row has `setup_status == "Actionable"` (all watchlist-only).
**Pass criteria:** `regime.label == "Risk-off"` AND count of rows with `setup_status == "Actionable"` is `0`.

### TC-04 — Older run's rankings/scores differ from the latest run (J-08 at API level)
**Type:** api
**Preconditions:** ≥2 runs persisted with different `asof_date`.

**Steps:**
1. From `/api/runs`, take the newest (`run_id` of max `asof_date`) and an older run.
2. `curl` both `/api/runs/{id}` detail payloads.
3. Pick a ticker present in both runs; compare its `leadership_score` (and top-of-table ranking order).

**Expected outcome:** A common ticker's stored Leadership score and/or the ranking order differs between the older and latest runs — proving each is a frozen as-of view, not a recomputation of today.
**Pass criteria:** At least one common ticker's stored score differs between the two runs, OR the top-N ranked tickers differ between runs.

### TC-05 — Unknown `run_id` returns 404 (no fabricated run)
**Type:** api
**Preconditions:** Backend up.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/runs/999999`

**Expected outcome:** `404` with an honest not-found body; no synthesized run returned.
**Pass criteria:** Status code is `404`.

### TC-06 — Snapshot persistence is complete + idempotent + immutable
**Type:** artifact / unit
**Preconditions:** Backend test suite available (`apps/backend/tests/`).

**Steps:**
1. Run `pytest apps/backend/tests/test_scanner.py -q`.
2. Confirm `test_run_scan_persists_complete_snapshot`, `test_run_scan_idempotent_and_immutable` execute.

**Expected outcome:** Run + result/sector/theme child rows all written for an as-of date; calling `run_scan`/`bootstrap_runs` twice for the same date yields exactly ONE run with identical `id`/`created_at` and byte-identical child rows (no duplicate, no UPDATE).
**Pass criteria:** Both named tests PASS; no second `ScannerRun` row created for a repeated date.

### TC-07 — No-lookahead: a run dated D is unaffected by bars dated > D
**Type:** unit
**Preconditions:** Backend test suite available.

**Steps:**
1. Run `pytest apps/backend/tests/test_scanner.py::test_run_scan_no_lookahead -q`.

**Expected outcome:** The run computed for date D equals the run computed against a DB truncated to bars ≤ D; no future bar influences the as-of score.
**Pass criteria:** Test PASSES.

### TC-08 — Latest stored snapshot is faithful to the live engine (single-source)
**Type:** unit
**Preconditions:** Backend test suite available.

**Steps:**
1. Run `pytest apps/backend/tests/test_scanner.py::test_latest_run_faithful_to_live_computation -q`.

**Expected outcome:** The latest persisted run's per-stock `record_json` equals `score_stocks(latest)["rows"]` and `regime_*` equals `score_regime(latest)`, field-by-field — one value, two read paths, never two computations.
**Pass criteria:** Test PASSES (field-by-field equality).

### TC-09 — No magic numbers: bootstrap dates come from config
**Type:** unit
**Preconditions:** Backend test suite available; `config.yaml` has `scanner.bootstrap_dates`.

**Steps:**
1. Run `pytest apps/backend/tests/test_no_magic_numbers.py -q`.

**Expected outcome:** The scanner's bootstrap dates are read from `config.scanner.bootstrap_dates` (parsed via `date.fromisoformat`); no date literal in calc code; the scanner introduces no new scoring literal.
**Pass criteria:** Test suite PASSES with the scanner extension included.

### TC-10 — Full backend suite + frontend build
**Type:** artifact
**Preconditions:** Repo at iter-5 dev-complete state.

**Steps:**
1. Run the backend test command (`pytest`) from `.claude/project-template.md`.
2. Run `npm run build` in `apps/frontend`.

**Expected outcome:** All backend tests green (incl. new scanner + api-runs cases); frontend build typechecks all routes including the two new scanner-runs pages.
**Pass criteria:** `pytest` exit 0, 0 failures; `npm run build` exit 0 with no type errors.

### TC-11 — `/scanner-runs` list page renders the dated run history (browser)
**Type:** browser
**Preconditions:** Backend `:8000` and frontend `:3000` running.

**Steps:**
1. Navigate to `http://localhost:3000/scanner-runs`.
2. Observe the table of runs.
3. Screenshot to `reports/qa/goal-i_can_see_the_wealthy_future-iter-5-evidence/TC-11-scanner-runs-list.png`.

**Expected outcome:** A dense dark table with ≥2 rows: as-of date, colour-graded regime badge (label + score; Risk-off clearly labelled), candidate counts (Actionable / Breakout-watch / Pullback-watch), stock count. Rows link to `/scanner-runs/[runId]`.
**Pass criteria:** ≥2 dated rows visible; a Risk-off-labelled row is present; clicking a row navigates to its detail page.

### TC-12 — J-07: open the Risk-Off run, confirm regime + zero Actionable (browser)
**Type:** browser
**Preconditions:** List page reachable; a Risk-off run exists.

**Steps:**
1. From `/scanner-runs`, click the Risk-off-labelled run.
2. On `/scanner-runs/[runId]`, read the regime panel and the "Immutable snapshot — as of YYYY-MM-DD" header.
3. Scan the stored stock table's setup-status column.
4. Screenshot to `.../TC-12-risk-off-detail.png`.

**Expected outcome:** Header shows immutable/as-of framing with the run's date; regime panel reads `Risk-off`; no stock row shows setup status `Actionable` (all watchlist-only).
**Pass criteria:** Regime panel displays `Risk-off` AND zero "Actionable" setups visible in the table.

### TC-13 — J-08: older run's rankings differ from latest (browser)
**Type:** browser
**Preconditions:** ≥2 dated runs reachable from the list.

**Steps:**
1. Open an older run; note its top tickers/scores.
2. Navigate back; open the latest run; note its top tickers/scores.
3. Compare the two; screenshot both to `.../TC-13-older.png` and `.../TC-13-latest.png`.

**Expected outcome:** The older run's stored rankings/scores visibly differ from the latest run's — confirming each snapshot is a frozen as-of view, not a recomputation of today.
**Pass criteria:** Top tickers and/or a common ticker's score differ between the older and latest detail pages.

### TC-14 — Honest unavailable / 404 states (browser)
**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. With backend stopped (or via a bad id), load `/scanner-runs` and `/scanner-runs/999999`.
2. Screenshot to `.../TC-14-unavailable.png`.

**Expected outcome:** Explicit "Backend unavailable" / empty / not-found states — never fabricated runs or scores.
**Pass criteria:** An explicit error/empty/404 state is shown; no fake data rendered.

### TC-15 — Regression sweep J-01–J-06 unregressed (browser)
**Type:** browser
**Preconditions:** Backend + frontend running.

**Steps:**
1. Re-shoot J-01 dashboard (`/`), J-02 stock leaderboard + filters (`/stocks`), J-03 themes (`/themes`), J-04 sectors (`/sectors`), J-05 stock detail chart (`/stocks/[ticker]`), J-06 list==detail consistency (same symbol's scores match between leaderboard and detail).
2. Save screenshots under the evidence dir (`TC-15-j0X-*.png`).

**Expected outcome:** All six prior journeys render and behave as before; live endpoints unchanged so no regression.
**Pass criteria:** Each page loads with real data; J-06 — a sampled symbol's six scores/bucket/setup are identical between leaderboard and detail (and identical to its stored snapshot row).

### TC-16 — Audit handoff emitted
**Type:** artifact
**Preconditions:** Iteration audit step has run.

**Steps:**
1. Check `reports/audits/goal-i_can_see_the_wealthy_future-iter-5-audit.md` exists and is non-empty.

**Expected outcome:** Audit handoff present (owed 4 prior full-depth iters per spec DoD).
**Pass criteria:** File exists with a verdict line and findings.

## Summary

Total test cases: 16
- API tests: 5 (TC-01–TC-05)
- Browser tests: 6 (TC-11–TC-15 — TC-15 covers J-01–J-06 regression)
- Unit tests: 3 (TC-07, TC-08, TC-09)
- Artifact / mixed checks: 3 (TC-06 artifact+unit, TC-10 build/suite, TC-16 audit handoff)

**Critical anti-goal coverage:** Snapshots-immutable (TC-06), No-lookahead (TC-07), Single-source faithful copy (TC-08), Risk-Off-gates-Actionable / J-07 (TC-03, TC-12), No-fabrication (TC-05, TC-14), No-magic-numbers (TC-09). J-08 covered by TC-04 (API) + TC-13 (browser). DoD audit handoff covered by TC-16.
