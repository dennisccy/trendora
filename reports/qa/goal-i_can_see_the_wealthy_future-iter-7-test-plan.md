# goal-i_can_see_the_wealthy_future-iter-7 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Frontend Present:** yes

## Phase Goal

Deliver **J-11 (Watchlist with persistence)** — the last Must-have journey: a user can open `/watchlist`, add a stock with a free-text reason, see it listed with date-added, reason, *current* canonical Leadership/Entry Quality/Risk (A–E + number), setup status, a price-since-added figure, and an invalidation level, remove entries, and trust the entry **survives a backend restart** (DB-backed) — all while J-01–J-10 stay green and no anti-goal (single-source, no order path, no fabricated data, immutable snapshots) is violated.

**Service URLs:** Backend `http://localhost:8835`, Frontend `http://localhost:3835`. Valid universe ticker for tests: `ANET`. Unknown ticker for rejection tests: `ZZZZ`.

## Test Cases

### TC-01 — POST add a valid ticker returns enriched entry

**Type:** api
**Preconditions:** Backend running on :8835; seed loaded; `ANET` not yet on the watchlist.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X POST http://localhost:8835/api/watchlist -H "Content-Type: application/json" -d '{"ticker":"ANET","reason":"ANET — strong leader, watching pullback"}'`

**Expected outcome:** `200`/`201`; body is an enriched GET-shaped row containing `ticker:"ANET"`, the `reason`, `date_added`, `id`, the three current scores `{score,bucket}` (Leadership/Entry/Risk), `setup` `{status,reason}`, `invalidation`, and `price_since_added`.
**Pass criteria:** Status is 2xx AND every listed field is present (no score field is null/missing) AND `ticker == "ANET"`.

---

### TC-02 — GET watchlist lists the added entry with all required fields

**Type:** api
**Preconditions:** TC-01 succeeded (ANET on the list).

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8835/api/watchlist`

**Expected outcome:** `200`; a JSON array; the ANET entry carries `date_added`, `reason`, `leadership/entry/risk {score,bucket}`, `setup.status`, `invalidation`, `price_since_added`, `id`.
**Pass criteria:** Status 200 AND the ANET object contains all eight field groups, none null where a value is expected.

---

### TC-03 — Single-source equality: watchlist scores == /api/stocks row (byte-identical)

**Type:** api
**Preconditions:** ANET on the watchlist; backend running.

**Steps:**
1. Fetch `GET /api/watchlist`, extract the ANET entry's Leadership/Entry/Risk `{score,bucket}`, `setup.{status,reason}`, and `invalidation`.
2. Fetch `GET /api/stocks`, extract the ANET row's same fields.
3. Compare each field value-for-value.

**Expected outcome:** The current score, bucket, setup status/reason, and invalidation are identical between the two endpoints.
**Pass criteria:** Every compared field is byte-identical (J-06 extended to the write surface). Any divergence = FAIL (single-source anti-goal violation).

---

### TC-04 — Duplicate POST creates no duplicate row

**Type:** api
**Preconditions:** ANET already on the watchlist (TC-01).

**Steps:**
1. POST `{"ticker":"ANET","reason":"second attempt"}` again.
2. `GET /api/watchlist` and count ANET entries.

**Expected outcome:** Either `409 Conflict` OR an idempotent reason-update (2xx) — developer's choice; never a second row.
**Pass criteria:** Exactly ONE ANET entry exists after step 2, regardless of which response strategy was chosen.

---

### TC-05 — Unknown ticker rejected (no fabricated row)

**Type:** api
**Preconditions:** Backend running; `ZZZZ` not in `config.universe.symbols`.

**Steps:**
1. POST `{"ticker":"ZZZZ","reason":"not real"}`.
2. `GET /api/watchlist`.

**Expected outcome:** Status `422` or `404`; no `ZZZZ` row created.
**Pass criteria:** Status is 422/404 AND `GET /api/watchlist` contains no `ZZZZ` entry.

---

### TC-06 — DELETE removes an entry; DELETE of missing entry 404s

**Type:** api
**Preconditions:** ANET on the watchlist with a known `id`.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X DELETE http://localhost:8835/api/watchlist/<id>` for the ANET id.
2. `GET /api/watchlist` — confirm ANET gone.
3. `DELETE http://localhost:8835/api/watchlist/<same-id>` again (now absent).

**Expected outcome:** Step 1 returns 2xx and removes the row; step 3 returns `404`.
**Pass criteria:** Step 1 succeeds AND ANET absent in step 2 AND step 3 returns 404.

---

### TC-07 — price_since_added is honest, not fabricated

**Type:** api
**Preconditions:** ANET added against the frozen seed (latest date `2026-05-28`).

**Steps:**
1. `GET /api/watchlist`; read ANET `price_since_added`.

**Expected outcome:** A real number derived from the canonical price series — `0.00%` when `entry_close == current close` against the frozen seed (correct, not a defect), or `NA`/null when `entry_close` is null. Never a synthesized non-zero figure.
**Pass criteria:** `price_since_added` is `0.00%` (frozen seed) or an honest computed value / NA — and is clearly derived from `close_on`, not invented.

---

### TC-08 — Restart persistence (DB-backed crux) — unit/integration

**Type:** artifact
**Preconditions:** New file-backed test `apps/backend/tests/test_watchlist_persistence.py` exists.

**Steps:**
1. Confirm the test uses a **file-backed** temp SQLite path (`tmp_path`), NOT `:memory:`.
2. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_watchlist_persistence.py -v`.
3. Test must: add an entry via engine1 → `engine1.dispose()` → recreate engine against the same path → assert the entry is read back.

**Expected outcome:** Test passes, proving persistence is on-disk and survives engine recreation.
**Pass criteria:** Test file uses a file path (not `:memory:`) AND the test passes green.

---

### TC-09 — Immutability isolation: no snapshot/forward-return write

**Type:** artifact
**Preconditions:** New watchlist tests exist; backend test suite present.

**Steps:**
1. Run the immutability-isolation test in `test_api_watchlist.py` (add + remove a watchlist entry, assert no UPDATE/INSERT against `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns`).
2. Inspect `apps/backend/app/api/watchlist.py` source.

**Expected outcome:** Test passes; `watchlist.py` only touches the `watchlist` table.
**Pass criteria:** Isolation test green AND no write to any snapshot/forward-return table in source.

---

### TC-10 — No order/execution path (grep clean)

**Type:** artifact
**Preconditions:** Backend + frontend watchlist code written.

**Steps:**
1. Grep watchlist source (`app/api/watchlist.py`, `app/models.py` Watchlist, `app/watchlist/page.tsx`, `lib/api.ts`) for order/position verbs: `order|broker|buy|sell|quantity|shares|position|cost basis|P&L|pnl`.

**Expected outcome:** No order/position/portfolio field or verb present; `price_since_added` is informational only.
**Pass criteria:** Grep returns no order/execution/position match (excluding incidental words like "report"). Any genuine order-path token = FAIL.

---

### TC-11 — No magic numbers in watchlist code

**Type:** artifact
**Preconditions:** `app/api/watchlist.py` written.

**Steps:**
1. Inspect `app/api/watchlist.py` for any scoring weight, threshold, bucket edge, or decision-rule literal.
2. Run the existing `test_no_magic_numbers.py` guard.

**Expected outcome:** `watchlist.py` contains no scoring/threshold literal (it reads everything canonical from `score_stocks`/`close_on`); the existing guard stays green.
**Pass criteria:** No scoring/threshold literal in `watchlist.py` AND `test_no_magic_numbers.py` passes.

---

### TC-12 — Full backend unit suite + watchlist roundtrip green

**Type:** artifact
**Preconditions:** All backend changes in place.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`.

**Expected outcome:** Entire suite passes, including new add/get/delete roundtrip and error-case tests (422/404/409/503).
**Pass criteria:** Exit code 0; 0 failures; new watchlist tests present and passing.

---

### TC-13 — Frontend build typechecks/compiles

**Type:** artifact
**Preconditions:** `watchlist/page.tsx` and `lib/api.ts` changes in place.

**Steps:**
1. Run: `cd apps/frontend && npm run build`.

**Expected outcome:** Build compiles and typechecks all routes including `/watchlist`; `WatchlistEntry` type + mutating client calls resolve.
**Pass criteria:** Build exits 0 with no type errors.

---

### TC-14 — J-11 browser: add ANET, see all required fields (capture #1)

**Type:** browser
**Preconditions:** Backend :8835 and frontend :3835 running; watchlist empty.

**Steps:**
1. Navigate to `http://localhost:3835/watchlist` — confirm EmptyState (zero-entry case) renders.
2. In the Add control, enter ticker `ANET` and reason `ANET — strong leader, watching pullback`; click Add.
3. Wait for the list to refresh; locate the ANET row.
4. Screenshot to `reports/qa/goal-i_can_see_the_wealthy_future-iter-7-evidence/TC-14-entry-after-add.png`.

**Expected outcome:** Row shows ticker `ANET` (links to `/stocks/ANET`), date-added, the reason, current Leadership/Entry/Risk via ScoreBadge (A–E + number), setup status, price-since-added (signed %), and the invalidation note rendered verbatim.
**Pass criteria:** All listed fields visible in the row; screenshot saved (this is md5-distinct capture #1).

---

### TC-15 — J-11 browser: entry survives backend restart (capture #2)

**Type:** browser
**Preconditions:** TC-14 succeeded (ANET present in UI).

**Steps:**
1. Restart the backend (stop the uvicorn process on :8835, start it again via `bash scripts/start-backend.sh`); wait for `/api/health` to return ok.
2. Reload `http://localhost:3835/watchlist`.
3. Confirm the ANET row is still present with the same date-added/reason.
4. Screenshot to `reports/qa/goal-i_can_see_the_wealthy_future-iter-7-evidence/TC-15-entry-after-restart.png`.

**Expected outcome:** ANET entry persists across the restart (DB-backed), still showing all required fields.
**Pass criteria:** ANET row present after restart; screenshot saved and **md5-distinct** from TC-14's capture.

---

### TC-16 — J-11 browser: Remove deletes the row

**Type:** browser
**Preconditions:** ANET present in the UI.

**Steps:**
1. Click the per-row Remove button on the ANET row.
2. Confirm the row disappears (and EmptyState returns if it was the only entry).

**Expected outcome:** The entry is removed via DELETE and the list refreshes without it.
**Pass criteria:** ANET row no longer rendered after Remove.

---

### TC-17 — Add error path surfaces an honest inline error

**Type:** browser
**Preconditions:** Frontend running; watchlist supports add.

**Steps:**
1. In the Add control, enter an unknown ticker `ZZZZ` with any reason; click Add.

**Expected outcome:** An inline, honest error message (from the 422/404 response) — no fabricated success row added.
**Pass criteria:** Visible error shown AND no `ZZZZ` row appears in the table.

---

### TC-18 — Full regression sweep J-01–J-10 still green

**Type:** browser
**Preconditions:** Both services running.

**Steps:**
1. Re-confirm each prior journey on its page: J-01 (dashboard/regime), J-02 (actionable/risk-off gating), J-03 (stock leaderboard), J-04 (sector leaderboard), J-05 (stock detail + setup/invalidation), J-06 (list==detail single-source), J-07/J-08 (scanner runs/immutability), J-09/J-10 (forward returns/system health).
2. Capture evidence PNGs under the evidence dir; **hash (md5) each PNG** — where multiple journeys share one page, note it rather than counting a shared shot as independent proof.

**Expected outcome:** All ten journeys still pass; no regression from the additive watchlist work.
**Pass criteria:** Each of J-01–J-10 verified passing; evidence PNGs are md5-distinct per distinct page (shared-page reuse explicitly noted, not double-counted).

---

## Summary

Total test cases: **18**

| Type | Count | IDs |
|------|-------|-----|
| API | 7 | TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07 |
| Artifact | 6 | TC-08, TC-09, TC-10, TC-11, TC-12, TC-13 |
| Browser | 5 | TC-14, TC-15, TC-16, TC-17, TC-18 |

**Crux tests (must pass):** TC-08 (restart persistence, file-backed), TC-03 (single-source equality), TC-14 + TC-15 (J-11 add + restart, two md5-distinct captures), TC-18 (J-01–J-10 regression). Anti-goal guards: TC-09 (immutability isolation), TC-10 (no order path), TC-05/TC-07 (no fabricated data), TC-11 (no magic numbers).
