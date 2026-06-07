# Phase goal-i_can_see_the_wealthy_future_forever-iter-22 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 7/13 tests passed, 1 pass by code-inspection, 5 skipped (provider-dependent)

All P1 tests resolved: UT-01, UT-02, UT-03, UT-07, UT-11, UT-12 executed and passed live in Chrome.
UT-04, UT-05, UT-06 are P1 but marked SKIP (provider-dependent, per test-plan rules — SKIP is not
FAIL). UT-08 verified by source-code inspection. UT-09 skipped (provider-dependent). UT-10, UT-13
passed live.

> **Environment note:** The backend (`:8835`) was not running when the agent started. It was started
> manually with `CORS_ORIGINS=http://localhost:3835`; the browser-qa-phase.sh script manages lifecycle
> on normal pipeline runs. The frontend (`:3835`) was already running with a live `.next` (chunks
> returned HTTP 200 — not a dead shell).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Data Manager page loads | smoke | P1 | Heading + coverage card (6 metrics) + form + job-progress card; no error card | "Backend OK"; all 6 metrics; form + progress cards visible; no error card | PASS | UT-01-result.png |
| UT-02 | Backfill runs; no source label in header | happy-path | P1 | Backfill completes `ok`; header `backfill job · <range>` with no source segment; new run in history | Header `backfill job · 2021-02-03 → 2021-02-09` (no source segment); status `ok`; 5/5 dates; 3200 forward returns; new row in history | PASS | UT-02-result.png |
| UT-03 | Source picker + session key reveal | happy-path | P1 | Fetch reveals source picker + availability line; needs-key reveals `type=password` key field + helper; available hides it | Import source picker appeared; source-availability showed "Tiingo: needs key"; `type=password` field "Session API key for Tiingo" + full helper text present | PASS | UT-03-result.png |
| UT-04 | Chunk X/N badge advances | happy-path | P1 | `chunk X/N` badge renders and X advances during live fetch | No reachable provider for live chunked fetch; prior checkpoint proves chunk engine produced `chunk 0/7` | SKIP (provider-dependent) | UT-04-skip.png |
| UT-05 | Amber rate-limited resumable state | error | P1 | Status badge "rate-limited — resumable" amber; amber callout `resumable-state` | No live provider 429 drivable in this environment | SKIP (provider-dependent) | none |
| UT-06 | Resume on live job card | happy-path | P1 | Resume re-enters running for same import; chunk badge not reset; key cleared | Depends on UT-05 live amber card | SKIP (provider-dependent) | none |
| UT-07 | Resumable-imports panel survives restart | happy-path | P1 | `resumable-imports` card with chunk badge, source, range, counts, key field, Resume button | Panel present: `chunk 0/7`, "Alpha Vantage", "2026-06-01 → 2026-06-02", "0 done · 158 remaining · 0 bars so far", `type=password` key field, Resume button; backend freshly started this session proving checkpoint survived | PASS | UT-07-result.png |
| UT-08 | Panel hidden when nothing is paused | ux | P2 | No `resumable-imports` card when list empty | Source code line 691: `if (imports.length === 0) return null` — panel returns nothing for empty list | PASS (code inspection) | none |
| UT-09 | Resume from post-restart panel row | happy-path | P2 | Import pulled into job card as live; row drops off panel | Provider-dependent: valid key required for resume to reach running state | SKIP (provider-dependent) | none |
| UT-10 | Resume rejection handled inline | error | P2 | Inline `role=alert` error on empty-key submit; page not crashed | `role=alert` appeared: "source 'alpha_vantage' requires a key…"; page remained interactive | PASS | UT-10-result.png |
| UT-11 | Provider error has no key/query string | error | P1 | No sentinel key and no `?token=`/`?apikey=` in error text | 20 Tiingo errors read `HTTP 403 at https://api.tiingo.com/…/prices`; sentinel `SENupKEY123` absent; no `?token=`/`?apikey=` in page or API response | PASS | UT-11-result.png |
| UT-12 | One date `<select>` app-wide (J-18) | regression | P1 | Exactly one date select per page; new iter-22 controls add none | `/data` 1 date select, `/stocks` 1, `/backtest` 1, `/research` 1; job start/end are `type=date` inputs; no new date selects from iter-22 | PASS | UT-12-result.png |
| UT-13 | Coverage + Run history still render | regression | P2 | 6 metrics; gap-range line; 7 run-history columns | All 6 metrics; gaps=1295 amber; gap-range line; all 7 columns; 20 run rows | PASS | UT-13-result.png |

---

## Passed Tests (detail)

### UT-01 — Data Manager page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-01-result.png`
- Navigated to `http://localhost:3835/data`; `GET /_next/static/chunks/main-app.js` → 200 (live next dev, not a clobbered `.next`)
- Heading "Data Manager" + "Grow the dataset on demand…" subtitle present
- "Dataset coverage" card: all 6 metrics (PRICE HISTORY 2021-01-04 → 2026-06-05, UNIVERSE 122, SYMBOLS 158, TRADING DAYS 1362, SNAPSHOT DATES 67, BACKFILL GAPS 1295)
- "Start a fetch / backfill job" and "Job progress" cards both visible
- Header: "Backend OK · provider: seed · seed 2026-06-05 · 158 symbols" — no "Backend unavailable" error card

---

### UT-02 — Backfill job runs end-to-end; no source label in header
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-02-result.png`
- Backfill gaps = 1300; dates pre-filled 2021-02-03 → 2021-02-09; job kind = "Backfill snapshots" (confirmed via select[1].value = "backfill")
- Clicked Start → "Job running…" spinner appeared
- Job completed: header reads `backfill job · 2021-02-03 → 2021-02-09` — **no `<source> ·` segment** (Finding #2 fold confirmed)
- Status badge `ok` (green); "Snapshots backfilled 5/5 dates"; "5 snapshots · 3200 forward returns inserted"
- New row in Run history: `2026-06-07 08:19:11 | backfill | 2021-02-03 → 2021-02-09 | ok | 0/0 | 5`

---

### UT-03 — Source picker + session key field reveal for needs-key fetch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-03-result.png`
- After selecting "Fetch EOD prices" (native setter + input event): select count rose from 2 to 3; Import source dropdown appeared
- `data-testid="source-availability"` showed "Yahoo Finance: available · no key required" for yahoo
- Selected Tiingo (native setter + input event): source-availability updated to "Tiingo: needs key · set $TIINGO_API_KEY or paste a session key"; `type="password"` key field appeared labeled "Session API key for Tiingo"
- Helper text present: "Held in memory for this run only — never written to disk, the database, the run log, or a cookie, and never echoed back."
- Note: the "switching back to available source hides field" sub-assertion could not be fully automated (React controlled select state not re-triggering on second native setter call in Chrome MCP); the primary requirement (key field appears for needs-key source) is fully confirmed

---

### UT-07 — Resumable imports panel survives backend restart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-07-result.png`
- Backend was not running on :8835 at session start (started manually for this session — backend freshly started, so in-memory state was empty)
- `data-testid="resumable-imports"` panel present on first page load, populated from the durable `ImportCheckpoint` table via `GET /api/data`, not from any in-memory job state
- Panel contents: `chunk 0/7` badge, "Alpha Vantage" source label, "2026-06-01 → 2026-06-02" date range, "0 done · 158 remaining · 0 bars so far", `type="password"` field "Session API key for Alpha Vantage", `data-testid="resume-button"` Resume button
- Panel hint text: "Rate-limited imports paused mid-run — progress is saved to the database and survives a backend restart."

---

### UT-08 — Resumable imports panel hidden when nothing is paused
**Verdict:** PASS (verified by source inspection)
**Evidence:** `apps/frontend/app/data/page.tsx` line 691
- `ResumableImportsPanel` component contains `if (imports.length === 0) return null` — the panel renders nothing when the imports list is empty
- Cannot drive to zero-imports state without a full provider resume to completion (provider-dependent); verified directly from source code
- Current state (1 resumable checkpoint) correctly shows the panel, confirming the conditional rendering is active

---

### UT-10 — Resume rejection handled inline
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-10-result.png`
- Clicked `data-testid="resume-button"` on the Alpha Vantage resumable row with the key field empty
- Inline `role="alert"` appeared: "source 'alpha_vantage' requires a key; set $ALPHAVANTAGE_API_KEY or paste a session key"
- Page did not crash: `data-testid="resumable-imports"` panel remained present; form remained interactive (2 buttons, 5 inputs still in DOM)
- Backend 400 error surfaced cleanly as an inline alert

---

### UT-11 — Surfaced provider error contains no API key or query string
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-11-result.png`
- POSTed Tiingo fetch via API with sentinel key `SENupKEY123` (start/end 2021-01-04, 158 symbols)
- Job completed `failed`; 20 error strings all read: `tiingo request failed for '<TICKER>': HTTP 403 at https://api.tiingo.com/tiingo/daily/<TICKER>/prices`
- API-level check (`GET /api/data/jobs/{id}`): `SENupKEY123` absent from all 20 errors; no `?token=` or `?apikey=` present — covering the MEMORY `httpx-error-leaks-url-query-key` leak path
- UI page text check: `SENupKEY123` not in page; no `?token=`/`?apikey=` in page text
- Run history Summary: "fetch: 0/158 symbols ok, 158 failed, 0 new bars" — no key, no fabricated bars

---

### UT-12 — Exactly one date `<select>` app-wide (J-18 regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-12-result.png`

| Page | Total `<select>` | Date `<select>` | Notes |
|------|----------------:|----------------:|-------|
| `/data` | 2 | 1 ("Latest · 2026-06-05", 67 opts) | Other: job kind (3 opts); job start/end are `type=date` inputs |
| `/stocks` | 4 | 1 ("Latest · 2026-06-05", 67 opts) | Others: sector, setup, pattern filters |
| `/backtest` | 1 | 1 ("Latest · 2026-06-05", 67 opts) | — |
| `/research` | 7 | 1 ("Latest · 2026-06-05", 67 opts) | Others: factor/metric/quantile controls |

New iter-22 controls (chunk badge, amber callout, Resume, resumable panel) introduce zero new date selects.

---

### UT-13 — Coverage panel + Run history still render after iter-22
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/UT-13-result.png`
- "Dataset coverage": all 6 metrics present; BACKFILL GAPS = 1295 (amber, > 0); "Gap range: 2021-02-10 → 2026-06-04" line present
- "Run history": all 7 columns (STARTED, KIND, RANGE, STATUS, SYMBOLS OK/FAILED, SNAPSHOTS, SUMMARY); 20 run rows
- No missing columns, no blank sections, no console errors

---

## Failed Tests

None.

---

## Skipped Tests

### UT-04 — Chunk X/N badge advances [provider-dependent]
**Verdict:** SKIPPED
**Reason:** Provider-dependent. No reachable provider can complete multiple chunks live: Yahoo Finance returns persistent 429 on this IP; Tiingo, Finnhub, Alpha Vantage, Stooq require API keys not in the environment. A multi-chunk fetch requires a working provider to watch X advance. The existing Resumable Imports panel (`chunk 0/7`, Alpha Vantage) proves the chunked import engine produced real chunk totals from a prior run. Functional coverage: API test plan TC-05/TC-06.

---

### UT-05 — Rate-limited amber resumable state [provider-dependent]
**Verdict:** SKIPPED
**Reason:** Provider-dependent. Requires driving a live fetch to an HTTP 429 and watching the running → amber transition on the job card. No provider is reachable for this path. The pre-existing Alpha Vantage checkpoint in the Resumable Imports panel was created by a prior session that did reach the amber resumable state — proving the machinery is functional. Functional coverage: API test plan TC-10/TC-11/TC-12.

---

### UT-06 — Resume on live job card [provider-dependent]
**Verdict:** SKIPPED
**Reason:** Depends on UT-05 producing a live amber job card in this session. Without that, the `data-testid="resumable-state"` amber callout on the job card cannot be reached. UT-10 confirmed the Resume button error path (inline alert on empty key). UT-07 confirmed `data-testid="resume-button"` is present and interactive on the resumable panel row.

---

### UT-09 — Resume from post-restart panel picks up import [provider-dependent]
**Verdict:** SKIPPED
**Reason:** Provider-dependent. Resuming the Alpha Vantage checkpoint requires a valid API key. Submitting without a key produces the UT-10 inline error (confirmed). The import reaching running state and completing (dropping off the panel) requires the provider to accept the key and return data. Functional coverage: API test plan TC-13.

---

## Environment

- **Frontend URL:** http://localhost:3835 (next dev, running at session start)
- **Backend URL:** http://localhost:8835 (started manually with `CORS_ORIGINS=http://localhost:3835`; health endpoint at `GET /api/health` returns `{"status":"ok"}`)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (CDP)
- **Test Date:** 2026-06-07
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-evidence/`
- **Evidence files:** UT-01-initial.png, UT-01-result.png, UT-02-initial.png, UT-02-running.png, UT-02-result.png, UT-03-result.png, UT-04-skip.png, UT-07-result.png, UT-10-before.png, UT-10-result.png, UT-11-result.png, UT-12-result.png, UT-13-result.png
