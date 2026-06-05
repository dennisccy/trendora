**Verdict:** FAIL

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21
**Date:** 2026-06-05
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes
**Backend:** http://localhost:8835 (healthy, 200) · **Frontend:** http://localhost:3835 (healthy, 200; `_next/static/chunks/main-app.js` → 200, badge clear)

---

## TL;DR

J-33's catalog / availability / source-threading / UI machinery is well-built and almost entirely
correct — but QA found a **reproducible breach of the iteration's PRINCIPAL anti-goal**: a pasted
**session-only API key is echoed back in an API response and rendered in the browser job card**. When a
key-bearing provider (tiingo / finnhub / alpha_vantage) returns a non-2xx, the provider passes the key as
a `?token=`/`?apikey=` URL query param; httpx's `HTTPStatusError` string (which embeds the full URL) is
wrapped verbatim into `ProviderUnavailableError`, appended to `JobProgress.errors[]`, and served by
`GET /api/data/jobs/{id}` → then displayed in the `/data` job card. This directly fails the spec's
Definition-of-Done ("a pasted key is … absent from `GET /api/data/jobs/{id}`, and never logged"),
TC-05, TC-07, and TC-11.

The DB, the persisted `DataProviderRun` run-history, and `GET /api/data` are all **clean** — the leak is
confined to the **live in-memory job-status `errors[]`** path. Backend suite is fully green
(**502 passed, 4 skipped**) and the frontend typechecks clean; the leak slips through because the
key-never-persisted unit test exercises a *mocked* provider that raises a sanitized error and never hits
the real httpx-URL-in-exception path.

**This is a blocker. Overall verdict: FAIL.**

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/…-iter-21-dev.md` | ✅ present (8.7 KB) |
| `reports/reviews/…-iter-21-review.md` | ✅ PASS_WITH_NOTES |
| `runs/goal-i_can_see_the_wealthy_future_forever-iter-21/status.json` | ✅ present (`review_passed`) |
| `reports/qa/…-iter-21-test-plan.md` | ✅ present (14 TCs) |
| `runs/.../state/blueprint.md` iter-21 note + Data-Contract row | ✅ present; **no** `blueprint.reapproval-requested` marker |

---

## Step 2 — Backend test suite (full, run once)

```
cd apps/backend && .venv/bin/python -m pytest tests/ -q
502 passed, 4 skipped in 1450.80s (0:24:10)
PYTEST_EXIT=0
```

Full suite green, exit 0, no regressions in the 29 carried journeys (no DB regen). Log:
`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-test.log`.

> ⚠️ **Caveat — green suite ≠ anti-goal satisfied.** `test_data_manager.py::test_pasted_api_key_never_persisted`
> passes, but it injects a **mocked** provider whose `ProviderUnavailableError` carries no real request
> URL. The real `tiingo`/`finnhub`/`alpha_vantage` clients put the key in the URL query string and
> `_http.fetch_json` wraps `str(httpx.HTTPStatusError)` (which contains that URL) into the error — a path
> the unit test never exercises. The leak is therefore invisible to the unit suite and only surfaced
> under live API/browser testing (below).

## Step 3 — Frontend

```
cd apps/frontend && npx tsc --noEmit   → TSC_EXIT=0   (0 type errors)
```
Built against the live `next dev` server (200 on main-app.js; badge clear). `npm run build` against the
live `.next` deliberately NOT run (MEMORY `browser-qa-dead-shell-next-cache`); dev verified a throwaway
`NEXT_DIST_DIR=.next-verify` build.

---

## Step 3.5 / Step 4 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Config-driven catalog + boot validation | artifact | 5 sources in `config.yaml`; `default_source` no-key & ∈ catalog; `seed` excluded; `live_provider` Literal retired | catalog ids `[yahoo,tiingo,finnhub,alpha_vantage,stooq]`; `default_source: yahoo` (needs_key=false); `seed` excluded; `live_provider` absent | **PASS** | — |
| TC-02 | Boot validation → ConfigError | api | ConfigError on missing env_var / dup id / default∉catalog | covered by green unit tests (`test_config.py`) in the 502-pass suite | **PASS** | verified in suite + handoff |
| TC-03 | Env-detected availability, no key leaked | api | availability flips on env presence; output carries env-var name only | `/api/data` `sources` shows `{id,label,needs_key,env_var,supports_market_cap,available,reason}`; needs-key sources `available:false`, no env value/key in output | **PASS** | — |
| TC-04 | make_provider resolves all ids; raises, no fabrication | api | each id resolves; non-OK→ProviderUnavailableError; no bar; needs-key-no-key→explicit | unit tests green; live tiingo fetch returned `failed`, 158 failed, **bars=0** (no fabrication) | **PASS** | no live call in tests; live confirm incidental |
| TC-05 | **Key never persisted (principal anti-goal)** | api | sentinel in NONE of: DB, `/api/data`, **job-status**, run history, logs | DB ✅ clean, `/api/data` ✅ clean, run history ✅ clean, logs ✅ clean — **but `GET /api/data/jobs/{id}` `errors[]` CONTAINS `token=SENTINEL_QA_KEY_9c3f1a`** | **FAIL** | **BLOCKER** — see Anti-goal breach below |
| TC-06 | Source threading: default/unknown/needs-key | api | default→`default_source`; unknown→400/422; needs-key-no-key→explicit 400 | omitted→`yahoo` ✅; `nonexistent`→**400** "unknown import source…" ✅; `tiingo` no key→**400** "source 'tiingo' requires a key; set $TIINGO_API_KEY or paste a session key" ✅ | **PASS** | env-var name present in message |
| TC-07 | `/api/data` sources array; status/history exclude key | api | `sources` present; no key in `/api/data`, job-status, run history | `sources` ✅ (5 entries); `/api/data` ✅ no key; run history ✅ no key; **job-status `/api/data/jobs/{id}` LEAKS key in `errors[]`** | **FAIL** | same root cause as TC-05 |
| TC-08 | Catalog renders from config in UI | browser | named sources + availability tags, no hardcoded list | `<select aria-label="Import source">` lists `Yahoo Finance · available`, `Tiingo/Finnhub/Alpha Vantage/Stooq · needs key` (from `data.sources`) | **PASS** | evidence TC-08-import-source-catalog.png |
| TC-09 | Needs-key reveals session-only key field | browser | `type=password` field appears; not pre-filled | selecting `tiingo` reveals `input[type=password] aria-label="Session API key"`, value empty, autocomplete=off | **PASS** | evidence TC-09-session-key-field.png |
| TC-10 | Exactly one date selector (J-18) | browser | one date `<select>` app-wide; import dates are `type=date` | exactly **1** date `<select>` ("View as-of date"); Job-kind & Import-source are non-date selects; job dates are `type=date` inputs | **PASS** | no new date state |
| TC-11 | Walled fetch → explicit error, no fabricated bar, key not echoed | browser | explicit error; zero bars; key NOT in job card | explicit `failed` state ✅; **bars=0, no fabrication** ✅; **key IS echoed** — job card renders `job.errors` (incl. `?token=<key>` URL) via `page.tsx:512-524`, full string in `title=` attr | **FAIL** | same root cause as TC-05 |
| TC-12 | Existing backfill still runs (J-17) | browser/api | backfill completes; snapshots; J-17 unchanged | backfill 2024-01-03 → `ok`, 0 new snapshots (date already snapshotted; immutability respected); prior backfill run id=2 = ok, 1 snapshot, 670 fwd returns | **PASS** | J-17 preserved |
| TC-13 | Subtitle cleanup | artifact | "System Health evidence" → "Backtest evidence" | `page.tsx:170` now "…grow the **Backtest** evidence"; no "System Health evidence" remains | **PASS** | — |
| TC-14 | Suite green; frontend builds; artifacts | artifact | pytest exit 0; tsc clean; handoff + blueprint; no reapproval marker | 502 passed exit 0; tsc 0 errors; handoff + blueprint present; no reapproval marker | **PASS** | — |

**11/14 test cases passed.** The 3 failures (TC-05, TC-07, TC-11) are **one root-cause defect** — the
session-key leak in the live job-status `errors[]` path.

---

## 🔴 Anti-goal breach (BLOCKER) — session key echoed in a response & the UI

**Spec, verbatim:** *"a provider key MUST be read from the environment, or — if the user pastes one into
the import UI — held in memory for that run only, never written to disk, the run log, the DB, or any
committed file, and never echoed back in any response."* DoD: *"a unit test proves a pasted key is …
absent from `GET /api/data` and `GET /api/data/jobs/{id}`, and never logged."*

**Reproduction (live, offline — no test fabrication):**
```
POST /api/data/jobs  {"kind":"fetch","start":"2024-01-02","end":"2024-01-02",
                      "source":"tiingo","api_key":"SENTINEL_QA_KEY_9c3f1a"}
→ job runs, status:"failed", symbols_failed:158, bars_fetched:0   (no fabrication — good)

GET /api/data/jobs/4625e807dece462eb788e7e8d225ade8
→ errors: [
    "NVDA: tiingo request failed for 'NVDA': Client error '403 Forbidden' for url
     'https://api.tiingo.com/tiingo/daily/NVDA/prices?token=SENTINEL_QA_KEY_9c3f1a&format=json
      &startDate=2024-01-02&endDate=2024-01-02' …",
    … ×18 more, each containing token=SENTINEL_QA_KEY_9c3f1a … ]
```
The pasted **session key is echoed back verbatim** in the job-status response and, because the `/data`
job card renders `job.errors` (`apps/frontend/app/data/page.tsx:512-524`, full string in the `title`
tooltip), it is **displayed in the browser**.

**Root cause:**
- `apps/backend/app/data_providers/_http.py:41-42` — `except httpx.HTTPError as exc: raise
  ProviderUnavailableError(f"{label} request failed for {symbol!r}: {exc}")`. For a non-2xx,
  `str(exc)` is httpx's `Client error '403 …' for url '<FULL URL incl. token=KEY>'`.
- Providers placing the key in the URL query string: `tiingo_provider.py:46` (`token`),
  `finnhub_provider.py:53` (`token`), `alpha_vantage_provider.py:51` (`apikey`). Yahoo (no key) and
  Stooq (key ignored) are unaffected.
- `apps/backend/app/engine/data_manager.py:298` — `_record_error(prog, f"{symbol}: {exc}")` appends the
  leaking string to `JobProgress.errors[]`, which `GET /api/data/jobs/{id}` serves and the UI renders.

**Scope of leak:** `GET /api/data/jobs/{id}` response **and** the rendered `/data` job card. **Not**
leaked to: SQLite DB (all tables scanned — clean), `DataProviderRun` run-history, `GET /api/data`, or the
backend log (`/tmp/qa-backend-8835.log` — 0 hits). So the persisted/DB anti-goal clauses hold; the
**"never echoed back in any response"** clause and the explicit **DoD `GET /api/data/jobs/{id}`** clause
are violated.

**Suggested fix direction (for developer/auditor — NOT applied by QA):** redact the key before it can
enter an error string — e.g. in `_http.fetch_json`, derive the message from
`exc.request.url.copy_with(query=None)` / `response.status_code` instead of raw `str(exc)`, or scrub
known key/query-param values; and/or send provider keys via an Authorization header rather than a URL
query param. Then add a unit test that drives a **real** httpx `HTTPStatusError` (key in URL) through
`get_daily` → `JobProgress.errors` and asserts the sentinel is absent — closing the mocked-provider blind
spot.

---

## Step 4b — UI Evolution Audit

1. Did the UI evolve to reflect the new capability? **Yes** — `/data` JobForm gained a config-driven
   Import-source `<select>` with per-source availability tags + a conditional session-only password field.
2. Can the user see/understand/control it? **Yes** — sources, availability, key-required reason, and a
   write-only key field with honest helper text ("Held in memory for this run only — never written to
   disk, the database, the run log, or a cookie, and never echoed back").
3. Relying on old generic pages? **No** — additive on the approved `/data` home; J-18 holds (1 date select).
4. Technically complete but under-exposed? **No** — well-exposed.

**Verdict:** UI-PASS-WITH-GAPS — the surface is excellent, but the helper text's promise ("never echoed
back") is contradicted by the job card actually rendering the key inside provider error lines. The UI gap
is a symptom of the backend leak, not a separate UI defect.

*(Per qa.md, UI-FAIL would force overall FAIL; here the UI is UI-PASS-WITH-GAPS, but the overall verdict
is independently FAIL on the anti-goal/DoD breach.)*

---

## Browser checks — evidence

- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-evidence/TC-08-import-source-catalog.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-21-evidence/TC-09-session-key-field.png`

Native-setter + bubbling-`change` pattern used for the React `<select>` (MEMORY
`react-controlled-select-needs-native-setter`); live DOM asserted after each interaction.

---

## What is correct (so a retry stays scoped)

- Config-driven catalog (5 sources), `default_source: yahoo`, `seed` excluded, `live_provider` Literal retired — ✅
- Boot validation → `ConfigError` (dup id / missing env_var / default∉catalog) — ✅ (green unit tests)
- `compute_provider_availability` env-detected, env-var name only, no value/key — ✅
- `make_provider` resolves every id; non-OK/unparseable → `ProviderUnavailableError`; **zero fabricated bars** (live tiingo bars=0; live yahoo bars=0) — ✅
- Source threading: default applied, unknown→400, needs-key-no-key→explicit 400 with env-var name — ✅
- UI source picker from `data.sources`, session-only password field, J-18 (one date select) — ✅
- J-17 backfill preserved; subtitle fixed; blueprint note + Data-Contract row; no reapproval marker — ✅
- Full backend suite 502 passed / 4 skipped; frontend tsc clean — ✅

**The ONLY blocker is the session-key leak into `JobProgress.errors[]` → `GET /api/data/jobs/{id}` → job card.**

---

## Blockers

1. **[CRITICAL / anti-goal] Pasted session key echoed in `GET /api/data/jobs/{id}` and the `/data` job
   card** via `JobProgress.errors[]` (root cause `data_providers/_http.py:42` wrapping `str(httpx
   HTTPStatusError)`; key-in-URL providers tiingo/finnhub/alpha_vantage). Violates the principal anti-goal
   "Import keys are env-or-session, never persisted … never echoed back in any response" and DoD "absent
   from `GET /api/data/jobs/{id}`". Fails TC-05, TC-07, TC-11. **Must be fixed + covered by a real-error
   (non-mocked-URL) regression test before this iteration can pass.**

---

## Verdict

**Verdict:** FAIL
