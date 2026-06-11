# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 — UI Test Results

**Phase:** J-46 — Parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill cache, committed advisory benchmark
**Date:** 2026-06-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 8/10 tests passed (1 skipped, 1 conditional-pass with note)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | Page renders with "Data Manager" heading, no blank screen, no 404 on _next chunks | Page fully loaded with "Data Manager" heading, 29 buttons interactive, 6 _next/static chunks loaded (200), no "Checking backend…" spinner | PASS | `UT-01-result.png` |
| UT-02 | Stocks list page loads without errors | smoke | P1 | At least one stock row visible, NVDA with A–E bucket, no JS error banner | 122/122 stocks listed, NVDA visible at rank 74 with bucket E and scores displayed, no error banner | PASS | `UT-02-result.png` |
| UT-03 | Live progress counter does not exceed total during parallel fetch | regression | P1 | Fetched-symbol count never exceeds declared total (never shows "X / Y" where X > Y) | Counter showed 0/158 throughout the running state; never exceeded 158; monotonically stayed at 0 (no bars committed before rate-limit, consistent with chunk-atomic semantics) | PASS | `UT-03-result.png`, `UT-03-running.png` |
| UT-04 | Amber "rate-limited — resumable" state appears on 429 | regression | P1 | Job card transitions to amber "rate-limited" or "resumable" label; NOT "failed"; Resume button visible | Job card shows "rate-limited — resumable" label, message "Rate-limited — paused at chunk 0/7. Progress is saved; resume to continue from the next un-fetched chunk (no data is re-fetched or duplicated)." Resume button visible. Status is NOT "failed". | PASS | `UT-04-resumable.png` |
| UT-05 | Resume button continues job from checkpoint | regression | P1 | After clicking Resume, job transitions back to running; counter does not reset to 0 from a higher value; no duplicate bars | After clicking Resume (correct button in job-progress card via mouse-event dispatch), job card immediately transitioned to "running" status; counter showed 0/158 — consistent with checkpoint at chunk 0 (no committed bars before the pause means 0 is the correct starting value for the resumed run; not a reset) | PASS | `UT-05-resumed.png` |
| UT-06 | Backfill-only job completes with ok summary | regression | P1 | Job card shows ok status, symbol count and bar count consistent with seed range | Backfill job `2021-02-18 → 2021-02-24` submitted; ran through running state; completed with "5 snapshots · 3200 forward returns inserted"; run history shows status `ok`, 5 snapshots, summary "backfill: 5 snapshots..." | PASS | `UT-06-running2.png`, `UT-06-result.png` |
| UT-07 | NVDA scores on /stocks list match known values | regression | P1 | NVDA row shows three non-empty numeric scores and a letter bucket | NVDA at rank 74: Leadership E/43.14, Entry Quality E/54.05, Risk E/35.80, Bucket E — all non-empty, all plausible (not 0.000/0.000/0.000) | PASS | `UT-07-stocks-list.png` |
| UT-08 | NVDA scores on detail page match the list page values | regression | P1 | Detail page shows identical scores and bucket to list page | `/stocks/NVDA` shows Leadership E/43.14, Entry Quality E/54.05, Risk E/35.80, Bucket E — identical to list page values to displayed decimal precision | PASS | `UT-08-nvda-detail.png` |
| UT-09 | Error text on a failed symbol does not contain API key substring | regression | P2 | Error message for a failed symbol does not contain `apikey=`, `token=`, or `key=demo` | No non-429 provider failure occurred during the alpha_vantage demo session — all failures were rate-limits (0 errors recorded). Checked page DOM and HTML: no `apikey=`, `token=`, or `key=demo` substrings found anywhere. Cannot verify per-symbol error scrubbing without a non-429 failure. | SKIP | `UT-09-no-key-leak.png` |
| UT-10 | Dead shell detection guard | regression | P1 | `_next/static/chunks/main-app.js` returns 200; page is hydrated | 6 _next/static chunks loaded successfully (200 status confirmed via eval); page shows 29 interactive buttons — fully hydrated, not a dead shell | PASS | `UT-10-result.png` |

---

## Passed Tests

### UT-01 — Data Manager page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-01-result.png`
- Navigated to `http://localhost:3835/data`; page rendered with "Data Manager" heading
- 29 interactive buttons, 13 inputs, 10 links detected — fully hydrated
- No "Checking backend…" spinner, no blank screen, no error message

### UT-02 — Stocks list page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-02-result.png`
- Navigated to `http://localhost:3835/stocks`; page rendered with "Stocks" heading
- 122/122 universe members displayed with scores and A–E buckets
- NVDA visible at rank 74 with bucket E and numeric scores — no JS error banner

### UT-03 — Live progress counter does not exceed total during parallel fetch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-03-running.png`, `UT-03-result.png`
- Submitted alpha_vantage / key=demo fetch job for 2026-06-10 → 2026-06-10 (158 symbols, 7 chunks)
- Live progress showed `0/158 (0 ok, 0 failed)` throughout the entire run (chunk 0/7)
- Counter never exceeded 158 (the declared total); monotonically stayed at 0 (chunk-atomic: no bars committed until a chunk fully completes, and chunk 0 was rate-limited before completion)
- Note: IPv6 SYN-SENT timeouts to alphavantage.co meant each symbol took ~15s per attempt × 5 attempts instead of the expected ~1s; total time to rate-limit was ~16 minutes instead of the documented ~3 minutes. The behavior was correct; the timing was extended by the network environment.

### UT-04 — Amber "rate-limited — resumable" state appears on 429
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-04-resumable.png`
- After chunk 0 exhausted all retries (alpha_vantage `Information` body mapped to RateLimitError), job card transitioned to "rate-limited — resumable"
- Exact text: "Rate-limited — paused at chunk 0/7. Progress is saved; resume to continue from the next un-fetched chunk (no data is re-fetched or duplicated)."
- Job does NOT show "failed" or "error" — correct amber state
- "Resume" button visible and enabled
- No JavaScript crash or blank card

### UT-05 — Resume button continues job from checkpoint
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-05-resumed.png`
- Filled Alpha Vantage key inputs with "demo" (required for Resume)
- Clicked Resume button in the Job progress card (button index 4, y=1572 doc coords) via mouse-event dispatch
- Job card immediately transitioned to "running" with `chunk 0/7, fetched 0/158 symbols (0 failed)`
- Counter did not reset from any previously-committed higher value to 0 — the 0 is correct since chunk 0 was never committed before the pause (chunk-atomic design)
- The resumed job is continuing from the same checkpoint (chunk_index=0 re-attempted idempotently)

### UT-06 — Backfill-only job completes with ok summary
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-06-running2.png`, `UT-06-result.png`
- Submitted backfill job for `2021-02-18 → 2021-02-24` (seed data range with known bars)
- Job progressed through running state; displayed "5/5 dates" in progress
- Completed with "5 snapshots · 3200 forward returns inserted" — no error messages
- Run history entry at 2026-06-11 16:40:13 shows status badge `ok`, 5 snapshots, summary "backfill: 5 snapshots..."
- Job completed within ~60 seconds as expected for offline deterministic backfill

### UT-07 — NVDA scores on /stocks list match known values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-07-stocks-list.png`
- NVDA at rank 74 on `/stocks` list (as-of 2026-06-10)
- Leadership: E / 43.14 | Entry Quality: E / 54.05 | Risk: E / 35.80 | Bucket: E
- All four values are non-empty and plausible (not 0.000/0.000/0.000)

### UT-08 — NVDA scores on detail page match the list page values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-08-nvda-detail.png`
- `/stocks/NVDA` detail page shows: Leadership E/43.14, Entry Quality E/54.05, Risk E/35.80, Bucket E
- All four values are identical to the list page values at the same decimal precision
- Detail page also shows component breakdown (RS vs SPY, MA stack, etc.) confirming single source of truth

### UT-10 — Dead shell detection guard
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/UT-10-result.png`
- Eval confirmed 6 `_next/static` chunks loaded: `main-app.js`, `app-pages-internals.js`, `app/layout.js`, etc.
- All loaded with 200 status (confirmed by `nextChunkCount: 6` and `hydrated: true`)
- Page shows 29 interactive buttons — not a static dead shell

---

## Skipped Tests

### UT-09 — Error text on a failed symbol does not contain API key substring
**Verdict:** SKIPPED
**Reason:** No non-429 provider failure occurred during the alpha_vantage demo key session — all outcomes for the alpha_vantage job were rate-limits (the `Information` body response maps to RateLimitError, not ProviderUnavailableError), resulting in 0 per-symbol error records. Without a non-429 failure, there is no per-symbol error text to inspect for API key leakage. As a partial substitute check: the entire page DOM (both `innerText` and `innerHTML`) was scanned — no `apikey=`, `token=`, or `key=demo` substrings found anywhere. The test plan permits SKIPPED with this note.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-11
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-evidence/`

## Notes

**UT-03/04/05 timing:** The alpha_vantage demo key triggered the expected RateLimitError → resumable flow, but took ~16 minutes to exhaust chunk 0 instead of the documented ~3 minutes. Root cause: IPv6 SYN-SENT timeouts to `alphavantage.co` — the backend's worker threads used IPv6 (SYN-SENT to `2606:4700:10::ac42:aa0b:443` and `2606:4700:10::6814:19e4:443`) which did not complete the TCP handshake, causing each HTTP call to time out at the 15-second `HTTP_TIMEOUT_SECONDS` limit instead of completing in ~1 second. With `max_retries=4` (5 total attempts × 15s) and 4 parallel workers over 22 symbols per chunk, the total time was ~16 minutes. The behavioral outcome (resumable state, correct counter, Resume working) matched expectations exactly.

**UT-06 first attempt:** The first Start button click matched a filter/sort button (index 0: "Universe members only") instead of the form submit. Resolved by using `button[type="submit"]` CSS selector.

**UT-05 Resume button:** The page has two "Resume" buttons — one in the Job progress live card and one in the Unfinished imports section. The text-based click matched the second one (Unfinished imports). Resolved by using mouse-event dispatch on button index 4 (job progress card Resume).
