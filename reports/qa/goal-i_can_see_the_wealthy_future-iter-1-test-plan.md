# goal-i_can_see_the_wealthy_future-iter-1 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Frontend Present:** yes

## Phase Goal

Stand up the deterministic offline spine — a FastAPI backend booting against a committed, frozen, real-history Stooq seed that answers `GET /api/health`, a config-driven universe (`config.yaml`), the SQLModel/SQLite iter-1 schema, the `PriceProvider`/`SeedProvider` abstraction, and a Next.js 15 navigable shell with health badge — with **no scoring and no journey data** (every page is a styled empty state; no J-* journey is expected to pass).

## Test Cases

### TC-01 — Backend boots offline and `/api/health` returns the contract shape

**Type:** api
**Preconditions:** Backend started via `scripts/start-backend.sh` (`--app-dir apps/backend`, `main:app`); committed seed present; no network access required.

**Steps:**
1. Start the backend with the start script (it loads config → create_all → loads seed if DB empty).
2. `curl -s -w "\n%{http_code}" http://localhost:<backend-port>/api/health`

**Expected outcome:** HTTP 200 with JSON `{"status":"ok","db_ok":true,"provider":"seed","last_run_date":null,"seed_latest_date":"<YYYY-MM-DD>","symbol_count":<n>}`.
**Pass criteria:** Status 200; `status=="ok"`, `db_ok==true`, `provider=="seed"`, `last_run_date` is `null`, `seed_latest_date` is a non-null date string, `symbol_count` is an integer > 0. No network call made during boot/request.

---

### TC-02 — Config loader returns typed settings (happy path)

**Type:** api
**Preconditions:** Repo-root `config.yaml` exists with `provider`, `database`, `universe`(+`filters`), ETF lists (`index`, `sector`, `industry`, `^VIX`), `themes`, `buckets`. pytest venv at `apps/backend/.venv`.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -v`

**Expected outcome:** `load_config()` reads repo-root `config.yaml` and returns typed (pydantic) settings exposing all iter-1 sections.
**Pass criteria:** Config-loader happy-path test passes; returned object exposes `provider`, `database`, non-empty `universe`, ETF lists, `themes`, `buckets`.

---

### TC-03 — Config loader rejects invalid/missing required keys (error case, no-magic-numbers contract)

**Type:** api
**Preconditions:** Test fixtures supply a config with an unknown `provider` (or a missing required key).

**Steps:**
1. Run the config error-case test in `tests/test_config.py`.

**Expected outcome:** An explicit error is raised on unknown `provider` / missing required key — not a silent default.
**Pass criteria:** Test asserts an exception (validation/explicit error) is raised; no fallback default value is substituted.

---

### TC-04 — SeedProvider determinism

**Type:** api
**Preconditions:** Committed seed fixture present under `apps/backend/data/seed/`.

**Steps:**
1. Run `tests/test_seed_provider.py` determinism test.

**Expected outcome:** A fixed `(symbol, start, end)` call to `SeedProvider.get_daily()` returns identical bars across repeated calls, matching the committed fixture exactly.
**Pass criteria:** Repeated-call results are byte/value-equal and match the fixture; test passes.

---

### TC-05 — Provider failure path surfaces explicit error (anti-goal: No fabricated data)

**Type:** api
**Preconditions:** Test simulates a missing symbol / unreadable fixture.

**Steps:**
1. Run the provider-failure test in `tests/test_seed_provider.py`.

**Expected outcome:** A missing symbol or unreadable fixture raises an explicit unavailable/raised error; the provider does **not** return synthesized or placeholder bars.
**Pass criteria:** Test asserts an error is raised (or explicit unavailable state) AND asserts no fabricated/placeholder bars are returned.

---

### TC-06 — Seed-integrity keystone: real bars span both regimes (anti-goal: No fabricated data)

**Type:** api
**Preconditions:** Committed real Stooq EOD seed present (≈3–4 yr window) covering universe + ETFs + `^VIX`.

**Steps:**
1. Run `tests/test_seed_integrity.py`.

**Expected outcome:** On the real committed SPY bars: a sustained **risk-off** stretch (contiguous ≈≥20 trading days with close < SMA200) AND a sustained **risk-on** stretch (contiguous ≈≥40 days with close > a *rising* SMA200) both exist; key universe symbols + index/sector ETFs + `^VIX` are present with reasonable bar counts and unique `(symbol, date)`.
**Pass criteria:** Both regime-stretch assertions pass on real bars; presence + bar-count + uniqueness assertions pass; no fabricated/hand-edited bars.

---

### TC-07 — DB schema = exactly the iter-1 tables

**Type:** api
**Preconditions:** Fresh DB; `create_all()` invoked.

**Steps:**
1. Run the schema test in `tests/test_db.py`.

**Expected outcome:** `create_all()` produces exactly: `stocks`, `etfs`, `sectors`, `industries`, `themes`, `theme_members`, `daily_prices` (unique + indexed `(symbol,date)`), `data_provider_runs` — and **none** of the deferred snapshot/score/forward/watchlist tables.
**Pass criteria:** Table set equals the iter-1 list exactly; deferred tables are absent; `daily_prices` has the `(symbol,date)` unique constraint + index.

---

### TC-08 — Idempotent seed load

**Type:** api
**Preconditions:** Fresh DB.

**Steps:**
1. Run the idempotency test in `tests/test_db.py` (load seed twice / boot twice).

**Expected outcome:** Loading the seed a second time adds no duplicate rows; a `data_provider_runs` row (provider=seed, symbols_ok/failed, status) is logged.
**Pass criteria:** Row counts in `daily_prices` and reference tables are unchanged after the second load; `(symbol,date)` uniqueness holds; `data_provider_runs` row recorded.

---

### TC-09 — Health endpoint via TestClient

**Type:** api
**Preconditions:** TestClient over the FastAPI app with seeded DB.

**Steps:**
1. Run `tests/test_health.py`.

**Expected outcome:** `GET /api/health` → 200 with `status:"ok"`, `db_ok:true`, `provider:"seed"`, non-null `seed_latest_date`.
**Pass criteria:** Test passes; all four fields assert as specified.

---

### TC-10 — Full backend pytest suite passes

**Type:** api
**Preconditions:** `apps/backend/.venv` populated from pinned `requirements.txt`.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

**Expected outcome:** All backend unit/integration tests pass.
**Pass criteria:** pytest exit code 0; 0 failures, 0 errors.

---

### TC-11 — Frontend production build compiles + typechecks

**Type:** api
**Preconditions:** `apps/frontend` deps installed.

**Steps:**
1. `cd apps/frontend && npm run build`

**Expected outcome:** Next.js 15 build compiles and typechecks with no errors.
**Pass criteria:** Build exits 0; no TypeScript or compile errors.

---

### TC-12 — All seven sidebar routes load with sidebar + styled empty state

**Type:** browser
**Preconditions:** Both services up; frontend on its derived port; `NEXT_PUBLIC_API_URL` set.

**Steps:**
1. Chrome MCP navigate to each: `/`, `/stocks`, `/themes`, `/sectors`, `/scanner-runs`, `/system-health`, `/watchlist`.
2. For each, confirm HTTP 200, persistent left sidebar renders, and a styled empty-state panel renders (not a raw string).
3. Screenshot each under `reports/qa/<phase>-evidence/TC-12-<route>.png`.

**Expected outcome:** All 7 routes render the shell + a styled empty state in the dense-dark analytical palette.
**Pass criteria:** Each route returns 200; sidebar visible with all 7 destinations; each page shows a styled empty-state component (e.g. "No scan yet — results appear once the scanner runs").

---

### TC-13 — Detail-route stubs resolve

**Type:** browser
**Preconditions:** Both services up.

**Steps:**
1. Navigate to `/stocks/SOMETICKER` and `/scanner-runs/SOMERUNID`.
2. Confirm each resolves to a minimal empty-state page (not a 404/crash).

**Expected outcome:** Both dynamic detail routes render an empty-state stub.
**Pass criteria:** Both routes return 200 and render a styled empty-state page; no Next.js 404 or runtime error.

---

### TC-14 — Health badge shows backend connected (provider + latest seed date)

**Type:** browser
**Preconditions:** Both services up; backend reachable from the browser (CORS via `CORS_ORIGINS`).

**Steps:**
1. Load any page; observe the header/sidebar status badge.
2. Confirm it shows backend connectivity, `provider = seed`, and the latest seed date.
3. Screenshot under `reports/qa/<phase>-evidence/TC-14-health-badge.png`.

**Expected outcome:** Badge renders a "connected" state surfacing provider=seed and the seed_latest_date from `GET /api/health`.
**Pass criteria:** Badge visibly indicates connected; displays `seed` provider and a seed date; values are read from the live `/api/health` response (no client-side computed business values).

---

### TC-15 — Health badge shows explicit "backend unavailable" on failure (anti-goal: no fabricated "ok")

**Type:** browser
**Preconditions:** Frontend up; backend stopped/unreachable (or `/api/health` made to fail).

**Steps:**
1. Stop the backend (or point `NEXT_PUBLIC_API_URL` at a dead port).
2. Reload the frontend; observe the badge.
3. Screenshot under `reports/qa/<phase>-evidence/TC-15-backend-unavailable.png`.

**Expected outcome:** Badge renders an explicit "backend unavailable" state — never a fabricated "ok".
**Pass criteria:** Badge shows an unavailable/error state; does NOT show "ok" or a fabricated provider/date.

---

### TC-16 — No anti-goal violated: no secrets, no order/execution path, gitignore hygiene

**Type:** artifact
**Preconditions:** Repo at iter-1 HEAD.

**Steps:**
1. Confirm no hard-coded credentials/API keys/tokens in source (grep for key/secret/token literals in `apps/`).
2. Confirm `.gitignore` covers `.env*` (keeps `.env.example`), `*.db`/`*.db-journal`, `.venv/`, `node_modules/`, `.next/`.
3. Confirm `apps/backend/data/seed/` fixture IS tracked but `apps/backend/data/trendora.db` is NOT tracked.
4. Confirm no brokerage/order/portfolio/execution code path exists.

**Expected outcome:** No secrets committed; runtime DB ignored; seed fixture tracked; no order/execution code.
**Pass criteria:** No credential literals found; gitignore entries present; `trendora.db` untracked, seed fixture tracked; no order/brokerage code reachable.

---

### TC-17 — No-magic-numbers: tunables read only via config loader

**Type:** artifact
**Preconditions:** Repo at iter-1 HEAD.

**Steps:**
1. Inspect backend calculation/code paths for hard-coded universe entries, ETF tickers, theme definitions, or bucket edges.
2. Confirm these values originate from `config.yaml` via `app/config.py` (the only access path).

**Expected outcome:** No scoring/threshold/universe/theme/bucket literal appears in code; all come from config.
**Pass criteria:** No such literals in calculation code; values traced to `load_config()`.

---

### TC-18 — Committed seed fixture exists (reproducibility checkpoint)

**Type:** artifact
**Preconditions:** Repo at iter-1 HEAD.

**Steps:**
1. Verify `apps/backend/data/seed/` contains the committed frozen fixture (CSV/Parquet) and is tracked in git.
2. Verify dev handoff `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-1-dev.md` states whether the live Stooq ingest succeeded and the seed window + confirmed regime coverage.

**Expected outcome:** Committed real-EOD seed present; dev handoff documents window/regime coverage and ingest outcome.
**Pass criteria:** Seed files tracked in git; handoff exists and explicitly states ingest success + window + both-regime confirmation.

---

### TC-19 — No journey regresses (all J-01…J-11 remain failing — expected)

**Type:** artifact
**Preconditions:** Browser smoke (TC-12…TC-15) complete.

**Steps:**
1. Confirm the browser pass verified shell render + connectivity only, not any journey.
2. Record explicitly that no J-* journey is expected to pass this iteration.

**Expected outcome:** All 11 journeys remain `failing` (baseline state); none regressed.
**Pass criteria:** No journey previously passing is now failing (none were passing); report explicitly notes infra-only, no journey targeted.

---

## Summary

Total test cases: 19
- API tests: 10 (TC-01 – TC-11; TC-01 is live HTTP, TC-02–TC-11 are pytest/build)
- Browser tests: 4 (TC-12, TC-13, TC-14, TC-15)
- Artifact checks: 4 (TC-16, TC-17, TC-18, TC-19)

Note: TC-11 (frontend build) is grouped under API/command-execution for counting. Anti-goal coverage: No fabricated data (TC-05, TC-06, TC-15, TC-18), No magic numbers (TC-03, TC-17), No secrets in source (TC-16), No order/execution path (TC-16). This iteration is infrastructure-only — **no J-* journey is expected to pass**; the browser cases verify the shell renders, navigates, and connects to the backend.
