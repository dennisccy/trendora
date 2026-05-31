# goal-i_can_see_the_wealthy_future-iter-8 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Frontend Present:** yes

## Phase Goal

Re-point the five primary read endpoints (`/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`) to serve canonical values from the persisted immutable snapshot for a resolved as-of date (computed once via `run_scan`, then read from storage — never recomputed per request), and add a global top-bar as-of date switcher that time-travels Dashboard / Stocks / Themes / Sectors / Stock Detail to any past stored trading day with a clear "viewing as-of D (historical)" indicator.

Backend URL: `http://localhost:8835` · Frontend URL: `http://localhost:3835`

## Test Cases

### TC-01 — Default resolution serves latest stored snapshot & echoes asof_date

**Type:** api
**Preconditions:** Backend running on :8835; at least one stored `scanner_runs` row.

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8835/api/stocks`
2. `curl -s http://localhost:8835/api/dashboard`
3. `curl -s http://localhost:8835/api/sectors`
4. `curl -s http://localhost:8835/api/themes`

**Expected outcome:** Each returns HTTP 200 with rows from the latest stored snapshot and a top-level `asof_date` equal to the latest `scanner_runs.asof_date`.
**Pass criteria:** All four return 200; each payload contains `asof_date` matching the latest run date; `/api/stocks` returns a non-empty `rows` array.

---

### TC-02 — As-of query re-points endpoints to a past stored date

**Type:** api
**Preconditions:** ≥2 stored runs. Capture an older run date `D_OLD` and latest `D_LATEST` from `curl -s http://localhost:8835/api/runs`.

**Steps:**
1. `curl -s "http://localhost:8835/api/stocks?as_of=$D_OLD"`
2. `curl -s "http://localhost:8835/api/dashboard?as_of=$D_OLD"`
3. Compare against the latest (no-param) responses from TC-01.

**Expected outcome:** Each response echoes `asof_date == D_OLD` and its values match that date's stored Scanner Run, differing from `D_LATEST` where the snapshots differ.
**Pass criteria:** Echoed `asof_date == D_OLD` on every endpoint; at least one canonical value (regime score/label or a stock score) differs from the latest response, confirming a genuine re-point (not a latest fallback).

---

### TC-03 — Invalid as-of rejected with explicit 4xx (no fabrication)

**Type:** api
**Preconditions:** Backend running. Latest data date known.

**Steps:**
1. Future date: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/stocks?as_of=2099-01-01"`
2. Unparseable: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/stocks?as_of=not-a-date"`
3. Before history (no bar ≤ D): `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/stocks?as_of=1990-01-01"`

**Expected outcome:** Future → 400; unparseable → 422; before-history → 400 (any explicit 4xx is acceptable). No synthesized snapshot is created.
**Pass criteria:** Each request returns a 4xx status (400/404/422); none returns 200 with a fabricated snapshot; no new `scanner_runs` row is created for the bad date.

---

### TC-04 — Snapshot-served list↔detail coherence (J-06, byte-identical)

**Type:** api
**Preconditions:** Backend running; NVDA present in the snapshot.

**Steps:**
1. `curl -s http://localhost:8835/api/stocks` → extract NVDA's Leadership, Entry Quality, Risk scores + A–E buckets.
2. `curl -s http://localhost:8835/api/stocks/NVDA` → extract the same three scores + buckets.
3. Repeat both with `?as_of=$D_OLD`.

**Expected outcome:** The three scores and buckets are identical between list and detail at both latest and `D_OLD` — both served from the same stored row.
**Pass criteria:** NVDA's three scores + buckets are byte-identical between `/api/stocks` and `/api/stocks/NVDA` at latest AND at `D_OLD`.

---

### TC-05 — Watchlist coherence with latest stocks row (J-11)

**Type:** api
**Preconditions:** Backend running; at least one watchlist entry (e.g. add ANET) whose ticker also appears in `/api/stocks` latest.

**Steps:**
1. `curl -s http://localhost:8835/api/watchlist` → read the entry's current Leadership/Entry/Risk + bucket + setup + invalidation.
2. `curl -s http://localhost:8835/api/stocks` → read the same ticker's current values.

**Expected outcome:** Watchlist current values equal the latest `/api/stocks` row for that ticker (single source, same stored row).
**Pass criteria:** Leadership, Entry, Risk, bucket, setup, and invalidation are byte-identical between `/api/watchlist` and `/api/stocks` latest.

---

### TC-06 — Bars endpoint honors as_of with no lookahead

**Type:** api
**Preconditions:** Backend running; NVDA bars seeded.

**Steps:**
1. `curl -s "http://localhost:8835/api/stocks/NVDA/bars?as_of=$D_OLD"` → inspect returned OHLCV dates and MA series.
2. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/stocks/NVDA/bars?as_of=2099-01-01"` (future).
3. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/stocks/NVDA/bars?as_of=bad"` (unparseable).

**Expected outcome:** With `as_of=$D_OLD`, every returned bar has date ≤ `D_OLD` and the MA series covers only dates ≤ `D_OLD`; bad dates return 4xx.
**Pass criteria:** Max bar date ≤ `D_OLD` (no future-dated bar); MA series present and bounded by `D_OLD`; future/unparseable `as_of` → 4xx.

---

### TC-07 — Create-once / immutability on first view of a stored seed date

**Type:** artifact
**Preconditions:** Backend test DB; a seed trading day `D_NEW` with bars but not yet stored as a run (verified via resolver/integration test fixture).

**Steps:**
1. Run the create-once / immutability unit test: `cd apps/backend && .venv/bin/python -m pytest tests/test_scanner.py tests/test_asof_resolver.py -v -k "create_once or immutab"` (or the resolver test file the dev created).
2. Confirm the test asserts: first resolve of `D_NEW` INSERTs exactly one run + its child rows; a second resolve performs no UPDATE and creates no duplicate run/result/score rows (row counts + identity stable).

**Expected outcome:** Test passes, proving snapshot create-once and immutability for an on-demand date.
**Pass criteria:** Named test(s) PASS; assertions on row counts/identity present and green.

---

### TC-08 — No-lookahead on on-demand snapshot creation

**Type:** artifact
**Preconditions:** Backend test environment.

**Steps:**
1. Run the no-lookahead / walk-forward guard test: `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "lookahead or walk_forward"`.

**Expected outcome:** An as-of-D snapshot created on demand uses only bars with date ≤ D; no future bar influences any stored as-of score.
**Pass criteria:** No-lookahead test PASSES and explicitly covers the on-demand creation path.

---

### TC-09 — No-recompute assertion (read path serves storage, not live engine)

**Type:** artifact
**Preconditions:** Backend test environment.

**Steps:**
1. Run the no-recompute test: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_engine.py -v -k "no_recompute or recompute or spy"`.
2. Confirm it monkeypatches/spies the live engines (`score_regime`/`score_stocks`/`score_sectors`/`score_themes`) to raise (or counts calls) and asserts the re-pointed endpoints still return 200 from storage for an already-persisted date.

**Expected outcome:** Re-pointed endpoints serve stored values without invoking the live scoring/regime engines for a persisted date.
**Pass criteria:** Test PASSES; live engines are not called (or raise without affecting the 200 response) for an already-stored date.

---

### TC-10 — Full backend suite green (no regressions)

**Type:** artifact
**Preconditions:** Backend deps installed.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee reports/qa/goal-i_can_see_the_wealthy_future-iter-8-test.log`

**Expected outcome:** All tests pass; count ≥ 179 (iter-7 baseline) plus the new iter-8 tests.
**Pass criteria:** Exit code 0; 0 failures/errors; total ≥ 179 tests.

---

### TC-11 — J-15: Snapshot-served reads render fast & coherent (browser)

**Type:** browser
**Preconditions:** Frontend reachable at `http://localhost:3835`; backend at :8835 (with `CORS_ORIGINS` set to the frontend origin).

**Steps:**
1. Chrome MCP → navigate to `http://localhost:3835/stocks`; wait for the leaderboard rows; note timing.
2. Reload `/stocks` (warm load).
3. Navigate to `/`, then `/themes`, then `/sectors`; confirm each renders rows/panels.
4. Note a stock's three scores on `/stocks`, open its Stock Detail, compare.
5. Screenshot each to `reports/qa/goal-i_can_see_the_wealthy_future-iter-8-evidence/`.

**Expected outcome:** All pages render populated data from the stored snapshot; warm `/stocks` load is fast (< ~1.5 s); the stock's three scores match between leaderboard and detail.
**Pass criteria:** Rows/panels render on all four pages; warm load < ~1.5 s; leaderboard scores == detail scores (coherence).

---

### TC-12 — J-13: Global as-of switcher time-travels every page (browser)

**Type:** browser
**Preconditions:** Frontend + backend reachable; ≥2 stored run dates available from `/api/runs`.

**Steps:**
1. Navigate to `http://localhost:3835/`; open the top-bar as-of date switcher.
2. Select a past trading day `D_OLD`.
3. Confirm `/`, then `/stocks`, `/themes`, `/sectors` all reflect `D_OLD` (values match that date's Scanner Run, not the latest).
4. Confirm a clear "viewing as-of D (historical)" indicator is visible (amber `--warn` badge/banner).
5. Switch back to the latest date; confirm the current view is restored (indicator clears).
6. Capture **distinct, md5-checked** evidence: a historical view on ≥2 different pages + the historical indicator + the back-to-latest restore, saved to `reports/qa/goal-i_can_see_the_wealthy_future-iter-8-evidence/`.

**Expected outcome:** Selecting `D_OLD` re-points all pages to that date with values matching its Scanner Run; the historical indicator shows; switching back to latest restores the live view.
**Pass criteria:** ≥2 pages reflect `D_OLD`; the "(historical)" indicator with the resolved date is visible; back-to-latest restores the default view; the per-journey evidence PNGs have distinct md5 hashes (not one shared full-page capture).

---

### TC-13 — Regression smoke (browser)

**Type:** browser
**Preconditions:** Frontend + backend reachable.

**Steps:**
1. **J-01:** `/` — confirm dashboard regime/breadth panels render.
2. **J-02:** `/stocks` — apply a leaderboard filter; confirm rows update.
3. **J-06:** note NVDA's scores on `/stocks`, open `/stocks/NVDA`, compare.
4. **J-07:** `/scanner-runs` → open the Risk-Off-labelled run → confirm zero stocks are "Actionable".

**Expected outcome:** All four existing journeys still behave as before the read-path change.
**Pass criteria:** Dashboard panels render; filter changes the row set; NVDA list scores == detail scores; the Risk-Off run shows zero "Actionable" stocks.

---

## Summary

Total test cases: 13
- API tests: 6 (TC-01 … TC-06)
- Artifact checks: 4 (TC-07 … TC-10)
- Browser tests: 3 (TC-11 … TC-13)

Coverage map: J-15 → TC-11; J-13 → TC-12; J-06 → TC-04, TC-13; J-11 → TC-05; J-07/J-01/J-02 → TC-13; no-recompute/immutability/no-lookahead criticals → TC-07, TC-08, TC-09; error cases → TC-03, TC-06; default/echo resolution → TC-01, TC-02; full-suite regression → TC-10.
