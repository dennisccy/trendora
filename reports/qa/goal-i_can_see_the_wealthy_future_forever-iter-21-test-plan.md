# goal-i_can_see_the_wealthy_future_forever-iter-21 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

On `/data`, a user can open a config-driven **Import source** catalog (Yahoo, Stooq, Tiingo, Finnhub, Alpha Vantage) each marked **available** or **needs key** (with a session-only paste field), pick a source, and start an import against it — surfacing an explicit error on provider failure (never a fabricated bar), with any pasted key held in memory for the run only and verifiably absent from `/api/data`, run history, and the DB.

## Test Cases

### TC-01 — Config-driven catalog with boot validation

**Type:** artifact
**Preconditions:** `config.yaml` + `apps/backend/app/config.py` modified; backend importable.

**Steps:**
1. Inspect `config.yaml` for `data_manager.providers` (list of `{id, label, needs_key, env_var, supports_market_cap}` for `yahoo`, `stooq`, `tiingo`, `finnhub`, `alpha_vantage`) and `data_manager.default_source`.
2. Confirm `ProviderCatalogEntry`/`ProviderCatalogCfg` typed models exist in `config.py`; the 2-value `Literal` on the import/live provider is retired (catalog-validated instead).
3. Confirm `seed` is NOT in the import catalog (top-level `provider: seed` unchanged).

**Expected outcome:** Catalog is loaded from config, not hardcoded in calculation code; `default_source` is a no-key source (expected `yahoo`).
**Pass criteria:** All 5 sources present in `config.yaml`; `default_source` ∈ catalog and `needs_key: false`; `provider: seed` still present and excluded from the import catalog.

---

### TC-02 — Boot validation raises ConfigError on malformed catalog

**Type:** api
**Preconditions:** Boot-validation logic present; pytest harness available.

**Steps:**
1. Run the unit test(s) that load a catalog with (a) missing `env_var` when `needs_key: true`, (b) duplicate `id`, (c) `default_source ∉ catalog`.
2. Assert each case raises `ConfigError` at boot.

**Expected outcome:** Each malformed catalog rejected at boot.
**Pass criteria:** Three `ConfigError` assertions pass; no config silently accepted.

---

### TC-03 — Env-detected availability (no key value leaked)

**Type:** api
**Preconditions:** `compute_provider_availability(cfg)` implemented.

**Steps:**
1. Unit test: assert a `needs_key` source is `available: true` only when its `env_var` is set in `os.environ`, else `available: false` with a human `reason`.
2. Assert a no-key source is always `available: true`.
3. Assert the output contains the env-var **name** + boolean + reason ONLY — never the env value, never any key string.

**Expected outcome:** Availability computed at request time from env presence; no secret echoed.
**Pass criteria:** Availability flips with env-var presence; output JSON has no key/env-value; per-entry shape `{id,label,needs_key,env_var,supports_market_cap,available,reason}`.

---

### TC-04 — make_provider resolves every catalog id; raises on failure, never fabricates

**Type:** api
**Preconditions:** New provider clients (`yahoo`, `tiingo`, `finnhub`, `alpha_vantage`) added; `seed`/`stooq` retained; HTTP mocked.

**Steps:**
1. Unit test: `make_provider(id)` resolves each catalog `id` without error.
2. With mocked HTTP returning non-OK status / unparseable body, call `get_daily` for each new client.
3. Construct a `needs_key` provider with neither env key nor passed `api_key`.

**Expected outcome:** Each failure → `ProviderUnavailableError`; no `Bar` synthesized; missing-key → explicit "key required" error.
**Pass criteria:** All catalog ids resolve; every non-OK/unparseable mocked response raises `ProviderUnavailableError`; zero fabricated bars returned; needs-key-no-key raises explicit error. NO live network call.

---

### TC-05 — Key never persisted (principal anti-goal)

**Type:** api
**Preconditions:** Job threading of `source`/`api_key` implemented; injected/mocked provider.

**Steps:**
1. Run a data job (mocked provider) passing a known sentinel `api_key` string.
2. Assert the sentinel is absent from every `DataProviderRun` column.
3. Assert the sentinel is absent from `GET /api/data`, `GET /api/data/jobs/{id}`, and logs / `_persist_run` detail JSON.

**Expected outcome:** Pasted key held in memory for the run only; never written to DB, responses, or logs.
**Pass criteria:** Sentinel string found in NONE of: DB columns, `/api/data`, job-status response, run history, log output.

---

### TC-06 — Source threading: default, unknown, needs-key-without-key

**Type:** api
**Preconditions:** `JobCreate.source`/`api_key` wired; backend running.

**Steps:**
1. POST `/api/data/jobs` with `source` omitted → assert it defaults to `cfg.data_manager.default_source` (J-17 fetch preserved).
2. POST with an unknown `source` → assert `400`/`422`.
3. POST with a `needs_key` source and no env/pasted key → assert explicit `400` ("source `<id>` requires a key; set `$<ENV_VAR>` or paste a session key").

**Expected outcome:** Default applied; invalid/needs-key rejected explicitly, never silent no-op or fabrication.
**Pass criteria:** Omitted source job uses `default_source`; unknown → 400/422; needs-key-no-key → 400 with the env-var name in the message.

---

### TC-07 — GET /api/data exposes sources array; status/history exclude key

**Type:** api
**Preconditions:** `/api/data` extended; backend running on :8000.

**Steps:**
1. `curl -s http://localhost:8000/api/data` → inspect for a `sources` array matching `compute_provider_availability`.
2. `curl` a job-status and run-history response → confirm no key field.

**Expected outcome:** `sources` array present with per-source availability metadata; no key anywhere.
**Pass criteria:** `sources` is a non-empty array of the documented shape; no `api_key`/key value in `/api/data`, `/api/data/jobs/{id}`, or run history.

---

### TC-08 — Import source catalog renders from config in UI

**Type:** browser
**Preconditions:** Frontend on :3000 (health badge cleared; `_next/static/chunks/main-app.js` → 200); job kind set to a fetch (`fetch`/`both`).

**Steps:**
1. Navigate to `http://localhost:3000/data`.
2. Locate the **Import source** `<Select>` in the JobForm.
3. Read options and per-source availability tags ("available" / "needs key").

**Expected outcome:** The named config sources appear with correct availability; no hardcoded list.
**Pass criteria:** The catalog sources render from `data.sources`; each shows an availability tag; needs-key sources marked accordingly.

---

### TC-09 — Needs-key source reveals session-only key field

**Type:** browser
**Preconditions:** As TC-08; a needs-key source has no env key.

**Steps:**
1. Select a **needs-key** source using the native-setter + bubbling-`change` pattern (Chrome-MCP `select` does not fire React `onChange` here — MEMORY `react-controlled-select-needs-native-setter`).
2. Assert live DOM for a `type="password"` key paste field appearing.
3. Confirm the field is not pre-filled from any API response.

**Expected outcome:** Session-only key field appears for needs-key sources; write-only.
**Pass criteria:** `type="password"` field present after selecting needs-key source; value never echoed from API; field held in component state only.

---

### TC-10 — Exactly one date selector (J-18 — no second date control added)

**Type:** browser
**Preconditions:** As TC-08, after the source/key controls are present.

**Steps:**
1. On `/data`, count date `<select>` controls app-wide.
2. Confirm `/data` import dates remain `type="date"` job-parameter inputs (not a viewing-date `<select>`).

**Expected outcome:** Only the global header as-of switcher is a date `<select>`; source/key controls add no date state.
**Pass criteria:** Exactly one date `<select>` exists (the global header switcher); import dates are `type="date"` inputs; no new date state introduced.

---

### TC-11 — Fetch against walled source → explicit error, no fabricated bar, key not echoed

**Type:** browser
**Preconditions:** As TC-08; selected provider is unavailable/walled.

**Steps:**
1. Select a source, (paste a session key if needs-key), start a **fetch** job.
2. Observe the job card / run history as the provider fails.

**Expected outcome:** Explicit error/unavailable job state ("no data fabricated"); zero synthesized bars; the pasted key is not echoed in the job card or run history.
**Pass criteria:** Job surfaces explicit error/unavailable state; no fabricated bar appears; key string absent from the job card and run history.

---

### TC-12 — Existing backfill still runs end-to-end (J-17)

**Type:** browser
**Preconditions:** As TC-08; default (no-key) source; offline/deterministic seed path.

**Steps:**
1. Start a **backfill** with the default source (omit source ⇒ `default_source`).
2. Observe job completion and snapshot creation.

**Expected outcome:** Backfill runs deterministically offline and creates snapshots as before — no regression from the source-picker addition.
**Pass criteria:** Backfill job completes successfully; snapshots created; J-17 path unchanged.

---

### TC-13 — Opportunistic subtitle cleanup

**Type:** artifact
**Preconditions:** `apps/frontend/app/data/page.tsx` modified.

**Steps:**
1. Inspect `page.tsx` around line 141.

**Expected outcome:** Stale "grow the System Health evidence" subtitle replaced with "grow the Backtest evidence".
**Pass criteria:** No remaining "System Health evidence" string in the `/data` subtitle.

---

### TC-14 — Full backend suite green; frontend builds clean; no regressions

**Type:** artifact
**Preconditions:** All code merged; all inline config-test fixtures updated for new required fields (MEMORY `config-fixtures-need-new-required-keys`).

**Steps:**
1. Run pytest **once** (full suite ~14 min — MEMORY `backend-test-suite-runtime`; do not run two invocations concurrently).
2. Build the frontend to a separate dir / before `next dev`; typecheck.
3. Verify `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-21-dev.md` exists and `blueprint.md` has the additive iter-21 note + Data-Contract row (no `blueprint.reapproval-requested` marker).

**Expected outcome:** Suite green; frontend builds clean; handoff + blueprint present; no reapproval marker.
**Pass criteria:** pytest exit 0 with no new failures (29 carried journeys byte-identical, no DB regen); frontend typechecks/builds; dev handoff exists; blueprint updated; no reapproval marker file.

---

## Summary

Total test cases: 14
- API tests: 6 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07)
- Browser tests: 5 (TC-08, TC-09, TC-10, TC-11, TC-12)
- Artifact checks: 3 (TC-01, TC-13, TC-14)

**Critical anti-goal coverage:** TC-05 (key never persisted), TC-10 (exactly one date selector / J-18), TC-04 & TC-11 (no fabricated data on provider failure), TC-01/TC-03 (config-driven, no secrets/key value in source or output). All provider tests use injected/mocked HTTP — **no live network call** (live fetch is data-walled & non-halting per spec).
