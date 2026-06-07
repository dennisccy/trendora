# goal-i_can_see_the_wealthy_future_forever-iter-22 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-05
**Frontend Present:** yes

## Phase Goal

Two coupled deliverables on `/data`, in order: (1) **redact the import key-leak** so a pasted session-only API key is verifiably absent from every response, the job card, run history, the checkpoint, and the logs (gates J-33 → passing); then (2) build **J-34** — a chunked (x/N), rate-limit-resilient (429 → backoff → graceful `resumable` stop), durably-checkpointed, restart-surviving, **Resume**-able import with per-`(symbol, date)` idempotency.

## Test Cases

### TC-01 — Real-httpx key/query redaction at the error source

**Type:** api (pytest — `tests/test_provider_clients.py`)
**Preconditions:** Providers accept an injected `client=`; sentinel key e.g. `SENupKEY123`.

**Steps:**
1. Build `httpx.MockTransport(handler)` returning HTTP `429`, then a real `httpx.Client(transport=...)`.
2. Inject into `TiingoProvider`/`FinnhubProvider`/`AlphaVantageProvider` with the sentinel key in the URL query (`token`/`apikey`).
3. Trigger a fetch; capture the raised exception. Repeat with a handler returning a non-JSON body (unparseable branch).

**Expected outcome:** `ProviderUnavailableError` (429 → `RateLimitError` subclass) raised; message built from redacted URL + status.
**Pass criteria:** `str(exc)` contains **neither** the sentinel key **nor** any `?token=`/`?apikey=`/query string; the redacted URL has `query=None`. Both 429 and non-JSON-body branches pass. This path is unreachable by the old hard-coded `http://x` `_FakeResponse`.

---

### TC-02 — 429 status maps to RateLimitError (redacted)

**Type:** api (pytest)
**Preconditions:** TC-01 transport returning HTTP 429.

**Steps:**
1. Drive the real `_http.py` path with a 429 response.
2. Assert exception type and that `RateLimitError` is a subclass of `ProviderUnavailableError`.
3. Confirm Alpha Vantage `_parse` maps a throttle `Note`/`Information` body → `RateLimitError`.

**Expected outcome:** 429 distinguished from generic failure; existing `except ProviderUnavailableError` handlers still catch it.
**Pass criteria:** `isinstance(exc, RateLimitError)` and `isinstance(exc, ProviderUnavailableError)` both True; message still redacted (no key/query).

---

### TC-03 — End-to-end key absence through job → response → checkpoint → logs

**Type:** api (pytest — extend `test_pasted_api_key_never_persisted`, do NOT delete)
**Preconditions:** Injected provider raising an error built from a **real** `httpx.HTTPStatusError` carrying the sentinel key in the request URL.

**Steps:**
1. Run a fetch job with the pasted sentinel key.
2. Inspect `JobProgress.errors`, `GET /api/data/jobs/{id}`, the `ImportCheckpoint` row / `resumable_imports`, every `DataProviderRun` column, and `caplog`.

**Expected outcome:** Defense-in-depth key scrub + source redaction both active.
**Pass criteria:** The sentinel key string appears in **none** of the above sinks. (MEMORY `httpx-error-leaks-url-query-key`: grep the job-status response, not just DB/`/api/data`.)

---

### TC-04 — Chunk plan is config-driven; boot validation

**Type:** api (pytest — `tests/test_config.py` + `tests/test_data_manager.py`)
**Preconditions:** `config.yaml` `data_manager.import_chunking` with 6 tunables; fixtures updated in ALL inline config dicts (MEMORY `config-fixtures-need-new-required-keys`).

**Steps:**
1. Build a chunk plan; assert `chunk_total == ceil(symbols/symbol_batch_size) × ceil(days/date_window_days)`.
2. Vary `symbol_batch_size` / `date_window_days` → assert `chunk_total` changes accordingly.
3. Load config with a non-positive `import_chunking` value.

**Expected outcome:** Chunk count derives only from config; no chunk/backoff/sleep literal in `data_manager.py`/providers.
**Pass criteria:** `chunk_total` tracks config edits; a non-positive value raises `ConfigError` at boot.

---

### TC-05 — Backoff/retry honored; persistent 429 → resumable (not failed)

**Type:** api (pytest)
**Preconditions:** Injected provider scripted to raise `RateLimitError` for K attempts; `time.sleep` patched/injectable (record durations, do not wait — MEMORY `backend-test-suite-runtime`).

**Steps:**
1. Script `RateLimitError` for K < `max_retries` then success → assert the chunk retries with exponential backoff `min(base*2**attempt, cap)` (assert attempt count and recorded backoff durations).
2. Script `RateLimitError` beyond `max_retries`.

**Expected outcome:** Bounded retry, then graceful stop.
**Pass criteria:** Attempt count ≤ `max_retries`+1; on exhaustion the job/checkpoint `status == "resumable"` (distinct from `failed`); **nothing fabricated**; the loop does **not** raise or halt.

---

### TC-06 — Durable checkpoint + resume + per-(symbol,date) idempotency

**Type:** api (pytest)
**Preconditions:** Chunked job paused at chunk k; fresh DB session to simulate a restart.

**Steps:**
1. Run a chunked job that pauses at chunk k; open a **fresh DB session** and read the `ImportCheckpoint`.
2. Call `resume_data_job(import_id)`; let it continue.
3. Inspect `DailyPrice` rows and already-stored symbols.

**Expected outcome:** Checkpoint survives the session boundary; resume continues from the next un-fetched chunk.
**Pass criteria:** `ImportCheckpoint.next_chunk_index == k` (advanced only after a chunk fully completes); resume starts at k; **no `(symbol, date)` fetched or inserted twice** (no duplicate `DailyPrice`; already-stored symbols skipped via `_existing_dates`); `resumable_imports` lists the paused import.

---

### TC-07 — Resume error handling (404 / 409 / 400)

**Type:** api (curl — `tests/test_api_data.py`)
**Preconditions:** Backend running on :8000; one `resumable`, one `ok`, one unknown import_id.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/data/jobs/UNKNOWN_ID/resume` → expect `404`.
2. POST resume on an `ok`/`failed` import_id → expect `409`.
3. POST resume on a needs-key source with **no** `api_key` body → expect `400`.

**Expected outcome:** Non-resumable/unknown/missing-key resumes rejected explicitly.
**Pass criteria:** Status codes are 404 (unknown), 409 (ok/failed), 400 (needs-key with no key) — exactly, with no fabricated success.

---

### TC-08 — Key never on the checkpoint / resumable_imports

**Type:** api (pytest + curl)
**Preconditions:** A paused job whose run used the pasted sentinel key.

**Steps:**
1. Inspect every `ImportCheckpoint` column for the paused job.
2. `curl -s http://localhost:8000/api/data | grep SENupKEY123` (sentinel) — expect no match.

**Expected outcome:** Checkpoint and `resumable_imports` are key-free.
**Pass criteria:** Sentinel key absent from all `ImportCheckpoint` columns and from the `resumable_imports` payload; `grep` finds nothing.

---

### TC-09 — `GET /api/data` exposes resumable_imports shape

**Type:** api (curl)
**Preconditions:** At least one `resumable` checkpoint present.

**Steps:**
1. `curl -s http://localhost:8000/api/data | python3 -m json.tool`.

**Expected outcome:** Response carries `resumable_imports` (newest first) with `import_id`, source, kind, range, chunk progress, symbols done/remaining.
**Pass criteria:** `resumable_imports` array present, ordered newest-first, with the listed fields and **no key**; existing run-history panel data still present.

---

### TC-10 — Browser J-33 re-verify (UT-08): pasted key absent from job card

**Type:** browser (Chrome MCP, `/data`)
**Preconditions:** Frontend :3000 + backend :8000 up (`GET /_next/static/chunks/main-app.js` → 200, health badge cleared — MEMORY `browser-qa-dead-shell-next-cache`); provider walled.

**Steps:**
1. Navigate to `http://localhost:3000/data`.
2. Select a needs-key source (native-setter + bubbling change — MEMORY `react-controlled-select-needs-native-setter`); paste a dummy session key (`type="password"`).
3. Start a **fetch**; wait for the explicit error/unavailable job-card state.
4. Inspect the job-card error list and run history DOM for the pasted key string. Screenshot to `reports/qa/<phase>-evidence/UT-08-key-absent.png`.

**Expected outcome:** Explicit error state, no fabricated bar, key not echoed.
**Pass criteria:** The pasted key string is **absent** from the job-card error list and run history (the iter-21 `UT-08-FAIL-key-leak-in-job-card-errors.png` failure now passes); no fabricated price.

---

### TC-11 — Browser J-34: chunk x/N advancing

**Type:** browser (Chrome MCP, `/data`)
**Preconditions:** As TC-10; an import spanning multiple chunks.

**Steps:**
1. Start an import spanning multiple chunks (multi-symbol / multi-date-window).
2. Observe `JobProgressPanel`.

**Expected outcome:** Per-chunk progress visible alongside symbols/snapshots.
**Pass criteria:** Job card shows **chunk x/N** advancing (monospace `tabular-nums`); symbols/snapshots progress still shown.

---

### TC-12 — Browser J-34: rate-limit → amber resumable state + Resume button

**Type:** browser (Chrome MCP, `/data`)
**Preconditions:** Scripted-429 path drivable from the UI/injected provider.

**Steps:**
1. Drive the scripted-429 import.
2. Observe the job card transition through retry → paused.

**Expected outcome:** Retry then a graceful resumable pause, visually distinct from failed.
**Pass criteria:** Job card shows a retry, then a **distinct amber `--warn` "rate-limited — resumable"** state (NOT red `failed`) with symbols done vs remaining and a **Resume** button. Screenshot saved under evidence dir.

---

### TC-13 — Browser J-34: restart survival + Resume continues

**Type:** browser (Chrome MCP, `/data`)
**Preconditions:** A `resumable` import exists; restart backend **by port** (MEMORY `dev-server-cleanup-by-port`).

**Steps:**
1. With a resumable import present, restart the backend by port.
2. Reload `http://localhost:3000/data`.
3. Confirm the import is still listed as resumable (sourced from `GET /api/data`).
4. Click **Resume** (re-supply the session key for a needs-key source; field `type="password"`, cleared after submit).

**Expected outcome:** Affordance survives the restart; Resume continues from the next un-fetched chunk.
**Pass criteria:** Import still listed **resumable** after restart (no live in-memory job); Resume continues from the next chunk and progresses/completes with **no duplicate rows**; key field cleared after submit.

---

### TC-14 — Browser J-18: exactly one date selector app-wide

**Type:** browser (Chrome MCP)
**Preconditions:** Frontend up.

**Steps:**
1. On `/data`, confirm chunk/Resume controls add no date `<select>`; import dates remain `type="date"` job-parameter inputs.
2. Spot-check `/stocks`, `/backtest`, `/research` for the single global as-of `<select>`.

**Expected outcome:** No second independent date state introduced.
**Pass criteria:** Exactly **one** date `<select>` (the global header switcher) app-wide; import date inputs are `type="date"` job parameters, not a date control. (MEMORY `j18-asof-on-stocks-fetch-is-correct`.)

---

### TC-15 — Browser J-17: backfill still runs end-to-end (regression)

**Type:** browser (Chrome MCP, `/data`)
**Preconditions:** Frontend + backend up.

**Steps:**
1. Run a backfill (offline/deterministic) from `/data`.
2. Confirm it completes and snapshots are created.
3. Confirm the backfill-only job header shows **no source segment** (Finding #2 fold).

**Expected outcome:** Backfill unchanged; a sub-batch fetch completes as one chunk.
**Pass criteria:** Backfill completes, snapshots created; backfill-only header omits the source segment; a small fetch completes as a single chunk.

---

### TC-16 — Full backend suite green (run ONCE) + sleeps patched

**Type:** artifact (pytest log)
**Preconditions:** All other code complete; `time.sleep`/backoff patched or config-zeroed in 429-retry tests.

**Steps:**
1. Run the full backend pytest suite **once** (~14 min — MEMORY `backend-test-suite-runtime`; never two concurrent invocations).
2. Verify no regressions across the 502+ existing tests.

**Expected outcome:** Suite green; 429-retry tests add no wall-clock.
**Pass criteria:** Pytest exits 0; new tests (TC-01..08) pass; no regression; total runtime not ballooned by real backoff waits.

---

### TC-17 — Frontend typecheck + isolated build clean

**Type:** artifact (tsc / build log)
**Preconditions:** `lib/api.ts` + `page.tsx` changes complete.

**Steps:**
1. Run `tsc --noEmit`.
2. Build to a **separate dir / before** `next dev` (MEMORY `browser-qa-dead-shell-next-cache`); confirm `GET /_next/static/chunks/main-app.js` → 200.

**Expected outcome:** Types and build clean; dev shell hydrates.
**Pass criteria:** `tsc --noEmit` exits 0; isolated build succeeds; main-app chunk 200 and health badge clears before browser QA. Do NOT build against the live `next dev` `.next`.

---

### TC-18 — Blueprint + dev handoff artifacts

**Type:** artifact
**Preconditions:** Iteration complete.

**Steps:**
1. Verify `runs/goal-session-.../state/blueprint.md` has the additive iter-22 note, the checkpoint Data-Contract row, and the invariant-#3 clarification; **no reapproval marker**.
2. Verify `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-22-dev.md` exists with the **real** pytest summary line (no `__PYTEST_RESULT__` placeholder).

**Expected outcome:** Required artifacts present and non-vague.
**Pass criteria:** Blueprint additive-only (no `blueprint.reapproval-requested` marker); handoff has real pass/fail counts.

---

## Summary

Total test cases: **18**
- API tests: **9** (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09)
- Browser tests: **6** (TC-10, TC-11, TC-12, TC-13, TC-14, TC-15)
- Artifact checks: **3** (TC-16, TC-17, TC-18)

**Principal-risk focus:** TC-01/TC-03/TC-08/TC-10 jointly close the iter-21 key-leak anti-goal — verify in source (grep the live `GET /api/data/jobs/{id}` response, job card, checkpoint, and `resumable_imports`), not just via QA. **Required-still-passing:** TC-14 (J-18), TC-15 (J-17), read path (J-15) untouched. **Live fetch is data-walled & non-halting** — a successful live import is recorded honestly as NA/rate-limited and must not halt; prove machinery offline with an injected scripted-429 provider.
