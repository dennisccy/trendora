# Iter-26 Functional Test Plan — Close the Last Buildable Wave

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Frontend Present:** yes

## Phase Goal

Lift J-37, J-38, J-39, and J-35 from `partial` to `passing` by capturing their defining multi-step browser flows end-to-end against a deterministic, env-gated, offline `seed` import source + fixture DB; fix the J-38 Resume-without-key UX gap; verify all required journeys remain green; ship no regressions.

## Test Cases

### TC-01 — Seed Import Source Present When Flag Set

**Type:** api
**Preconditions:** Backend running; `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=true` env var set.

**Steps:**
1. `GET /api/data` → inspect `sources` array in response body.

**Expected outcome:** Response contains exactly one entry with `{id: "seed", label: "Seed (offline test data)", needs_key: false, supports_market_cap: true, available: true}`.
**Pass criteria:** `sources` array includes the seed entry; no other new entries present.

---

### TC-02 — Seed Import Source Absent When Flag Unset

**Type:** api
**Preconditions:** Backend running; `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` unset or set to `false`.

**Steps:**
1. `GET /api/data` → inspect `sources` array in response body.

**Expected outcome:** Response `sources` array does NOT contain any entry with `id: "seed"`.
**Pass criteria:** Seed entry is completely absent; all other sources match the default config catalog.

---

### TC-03 — Seed Job Routes Through Existing Engine

**Type:** api
**Preconditions:** Backend running; fixture DB loaded; `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=true`; an import job with `source: "seed"` is queued.

**Steps:**
1. `POST /api/data/jobs` with `{source: "seed", symbols: ["TEST"], date_range: {...}, ...}` → capture the job ID.
2. Poll `GET /api/data/jobs/{id}` until `status: "complete"` or error.
3. Inspect job response for `source: "seed"` and verify it dispatched through the chunked engine (check logs for `J-34 engine` path, not a parallel/second path).

**Expected outcome:** Job completes; logs show the job routed through `start_data_job` → J-34 engine → `screen_reasons` predicate (single existing path, no fork).
**Pass criteria:** Job reaches completion; no second/parallel fetch or screen rule invoked; job metadata shows `source: "seed"`.

---

### TC-04 — Pull Constructs Gap-Exact Request (J-37 Diagnostic)

**Type:** api
**Preconditions:** Fixture DB loaded with one symbol having no history, one with thin history, one with intra-series gap; `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=true`; `/data` page loads without error.

**Steps:**
1. Load `/data` in browser → navigate to Missing Data Diagnostic panel.
2. Verify diagnostic renders all three categories: no-history, thin-history, intra-series-gap, each showing the exact symbol and shortfall range.
3. Click "Pull the missing data" → intercept the `POST /api/data/jobs` network request.
4. Inspect request body: verify `symbols` array and `date_range: {start, end}` match EXACTLY the diagnosed gap, NOT the whole universe or window.

**Expected outcome:** Diagnostic renders all three categories with correct symbols/ranges; pull request body contains only the shortfall range.
**Pass criteria:** Request body `symbols` and `date_range` equal the diagnosed gap (verifiable via network inspector); no universe-wide or window-wide fetch.

---

### TC-05 — Pull Completes and Coverage Updates (J-37 Success)

**Type:** browser
**Preconditions:** Fixture DB loaded; diagnostic shows all three categories; pull request intercepted and body verified.

**Steps:**
1. Allow the pull job to execute over the `seed` source.
2. Wait for job to reach `status: "complete"` (poll `/api/data/jobs/{id}`).
3. Verify the diagnostic row shrinks or clears (no longer shows the shortfall).
4. Check the J-36 per-symbol coverage table → verify new bars are reflected for the pulled symbols.
5. Take a screenshot showing the updated coverage table with the new bars.

**Expected outcome:** Job completes without error; diagnostic row shrinks or clears; coverage table reflects the new pulled bars.
**Pass criteria:** Job status is `complete`; diagnostic no longer shows the gap; coverage table shows the new bars for all three symbols.

---

### TC-06 — Pull Over Missing Provider Surfaces Error (J-37 Error Path)

**Type:** api
**Preconditions:** Backend running; fixture DB loaded; configured with a provider that is unreachable or returns a rate-limit error.

**Steps:**
1. Attempt a pull over an unreachable provider.
2. Monitor job status until completion or error.
3. Inspect job response for `errors[]` field and job status.

**Expected outcome:** Job fails gracefully; `errors[]` contains a clear message (e.g. "Provider unreachable" or "Rate limited"); no synthetic bars are fabricated to clear the diagnostic.
**Pass criteria:** Job status is `failed` or `error`; `errors[]` is non-empty and human-readable; diagnostic row remains visible (not cleared).

---

### TC-07 — J-38 Resume Without Key Shows Inline Error and Retains Row

**Type:** browser
**Preconditions:** Fixture DB loaded; an unfinished resumable import with `needs_key: true` is in the `UnfinishedImportsPanel`; no session key is provided.

**Steps:**
1. On `/data`, locate the resumable import row in the Unfinished Imports panel.
2. Attempt to click "Resume" without entering a session key.
3. Verify the request fails with a 400 error.
4. Inspect the DOM for a visible inline error message (must have `role="alert"` or similar) near/on the Resume control.
5. Verify the row is still visible in the panel (not removed or hidden).
6. Take a screenshot showing the error and the retained row.

**Expected outcome:** Error message renders inline and is visible; the unfinished import row remains in the panel.
**Pass criteria:** DOM contains `role="alert"` text indicating the key is required; the row is still present in the panel after the 400; screenshots show distinct before/after states.

---

### TC-08 — J-38 Resume With Key Continues From Checkpoint (J-38 Success)

**Type:** browser
**Preconditions:** Fixture DB loaded; an unfinished resumable import with `needs_key: true` and a stored checkpoint (`next_chunk_index > 0`); the session key for the import provider is available.

**Steps:**
1. On `/data`, locate the resumable import in the Unfinished Imports panel.
2. Enter the session key into the Resume control.
3. Click "Resume" → capture the `POST /api/data/jobs` request and verify `next_chunk_index` is present and > 0.
4. Allow the job to complete.
5. Verify the job status reaches `complete`.
6. Inspect the job response to confirm it resumed from the checkpoint, not from the beginning.
7. Take a screenshot showing the resumed and completed row (or cleared row if the job completes all chunks).

**Expected outcome:** Resume request includes the checkpoint index; job completes successfully; the unfinished import row clears or updates to reflect completion.
**Pass criteria:** Job `status: "complete"`; `POST` request body contains `next_chunk_index` matching the stored checkpoint; the job ran from that checkpoint onward (verifiable via job log or chunk count).

---

### TC-09 — J-38 Resume Key Not Echoed in Job Card or Error

**Type:** api
**Preconditions:** Backend running; fixture DB loaded; a resume operation over a needs-key provider is attempted (both success and failure paths).

**Steps:**
1. Resume an import with a session key (use a real key or a test key).
2. Inspect the job response from `GET /api/data/jobs/{id}` (the job card).
3. Scan the entire job response (JSON) for the session key, `?token=`, or `?apikey=` query strings.
4. Attempt a resume without a key → inspect the error response for any leaked key material.
5. Grep the response body for the sentinel/test key or URL-encoded variants.

**Expected outcome:** Session key is never present in the job card, error message, or any response field; only the provider label and type information are visible.
**Pass criteria:** Session key is completely absent from all job-status responses; the key is held in memory only (not logged, not echoed, not stored in the DB).

---

### TC-10 — J-38 Retry and Dismiss Preserve Audit (J-38 Side Paths)

**Type:** browser
**Preconditions:** Fixture DB loaded; an unfinished import is in the panel with a Run History showing at least one prior attempt.

**Steps:**
1. On `/data`, locate the unfinished import.
2. Click "Retry" → verify the run history is preserved (does not reset); the job is requeued.
3. Dismiss the row (using "Dismiss" or the close control) → verify the audit record (`data_provider_runs`) is still in the DB and the row is removed from the panel.
4. Reload the page → verify the unfinished import no longer appears, but if you query the API directly, the audit record is still present.

**Expected outcome:** Retry preserves run history; Dismiss removes the row from the panel but leaves the audit trail intact.
**Pass criteria:** Run history entry count does not decrease on Retry; after Dismiss, the row is gone from `/data` but `GET /api/data` → `unfinished_imports` does not include it; audit table still holds the record.

---

### TC-11 — J-39 Confirm-Preview on Live Host (Non-Destructive)

**Type:** browser
**Preconditions:** Live host running; a symbol with user-added bars is present (not seed-only); J-39 Remove Data control is accessible on `/data`.

**Steps:**
1. On `/data`, click "Remove Data" for a symbol with user-added bars.
2. The preview/confirm panel should render showing: removable bars count + date range, protected committed-seed bars count + breakdown (labeled "committed seed"), and dependent cascade estimate.
3. Verify the preview uses the **preview endpoint** (does not delete anything).
4. Inspect the DOM to confirm the numbers are correct (removable count + cascade estimate are visible).
5. Do NOT click the destructive confirm button. Close the preview.
6. Reload `/data` → verify all bars are still present (nothing was deleted).

**Expected outcome:** Preview renders removable bars, protected seed count, and cascade estimate; no data is deleted; the preview endpoint is used.
**Pass criteria:** Preview panel displays all four pieces of information (removable count, range, seed count + reason, cascade estimate); bars remain after preview; page reload shows no deletions.

---

### TC-12 — J-39 Wholly-Seed Scope Refused (J-39 Edge Case)

**Type:** browser
**Preconditions:** Fixture DB loaded with a symbol that has ONLY seed bars (no user-added bars); J-39 Remove Data control is accessible.

**Steps:**
1. On `/data`, click "Remove Data" for a symbol that is 100% committed seed.
2. Verify an error message or disabled state is displayed.
3. Verify the message explicitly states the reason (e.g. "Cannot remove symbol — all bars are from committed seed").
4. Verify the destructive confirm button is disabled or hidden.

**Expected outcome:** UI refuses the removal with a clear reason; no deletion can proceed.
**Pass criteria:** Error message is visible and human-readable; the confirm button is not clickable; the symbol's bars remain after attempting the action.

---

### TC-13 — J-39 Destructive Confirm and Cascade (Fixture Only)

**Type:** browser
**Preconditions:** Fixture DB loaded with a symbol that has user-added bars + cascaded snapshots/forward-returns; J-39 Remove Data control is accessible.

**Steps:**
1. On `/data`, click "Remove Data" for a symbol with user-added bars.
2. Verify the preview shows removable bars, seed count, and cascade estimate.
3. Click the destructive "Confirm Remove" button.
4. Verify the job completes.
5. Reload `/data` → verify the removed bars are gone, the cascaded snapshots/forward-returns are also gone, but any immutable snapshot rows are retained.
6. Query the DB to verify: user-added bars are deleted, cascaded dependents are deleted, but `scanner_run` records and audit rows are preserved.

**Expected outcome:** Bars and cascaded dependents are deleted; immutable scanner snapshots are retained; audit trail is unchanged.
**Pass criteria:** User-added bars are absent; cascaded snapshots are absent; `scanner_run` records and `data_provider_runs` audit rows are still in the DB.

---

### TC-14 — J-35 Expand Universe End-to-End (Seed Source)

**Type:** browser
**Preconditions:** Fixture DB loaded; current universe is seeded with a known count (e.g. 3 symbols); J-35 Expand Universe control is accessible on `/data`; `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=true`.

**Steps:**
1. On `/data`, note the current universe count (e.g. "3 symbols").
2. Click "Expand Universe" → the expand panel shows selectable providers.
3. Select "Seed (offline test data)" as the provider.
4. Click "Expand" → the job is queued.
5. Poll the job until completion.
6. Reload `/data` → verify the universe-count increased (e.g. from 3 to 5 symbols).
7. Inspect the `/methodology` page → verify the universe size matches the expanded count.
8. Take a screenshot showing the grown universe count.

**Expected outcome:** Expand job completes over the seed source; universe count increases; `/methodology` reflects the new count.
**Pass criteria:** Job `status: "complete"`; universe count on `/data` is greater than the initial count; `/methodology` universe-size value matches the new count.

---

### TC-15 — J-35 Expand Omitted-With-Reason (J-35 Side Path)

**Type:** browser
**Preconditions:** Fixture DB loaded; expand job has completed; some symbols may have been omitted due to eligibility rules.

**Steps:**
1. On `/data`, after an expand has completed, check if there is an "Omitted symbols" or "Ineligible" list in the results.
2. Verify the list shows symbols + reason (e.g. "Market cap data unavailable for [symbol]").

**Expected outcome:** If any symbols were omitted, the UI displays them with a reason.
**Pass criteria:** Omitted list is present and readable (if applicable); each entry includes a symbol and a reason.

---

### TC-16 — J-35 Expand Over Non-Cap-Supporting Provider Blocked (Edge Case)

**Type:** api
**Preconditions:** Backend running; fixture DB loaded; a provider with `supports_market_cap: false` is available.

**Steps:**
1. Attempt to expand the universe using a provider with `supports_market_cap: false`.
2. Verify the request fails with a 400 or 403 error.
3. Inspect the error response for a reason message.

**Expected outcome:** Request fails; error message indicates the provider does not support market cap expansion.
**Pass criteria:** HTTP status is 4xx; error message is human-readable and explains the gate.

---

### TC-17 — J-18 Watch Risk — Exactly One Date Selector on /data

**Type:** browser
**Preconditions:** `/data` page is loaded; the phase has added the seed source and the J-38 Resume error feedback.

**Steps:**
1. Load `/data`.
2. Inspect the DOM for all `<select>` elements with date-related attributes or `name` containing "date" or "as_of".
3. Count the number of date-picker controls.
4. Verify there is exactly one global as-of date selector (the existing one).
5. Verify no new date input, picker, or state selector was added by the seed source or the J-38 fix.

**Expected outcome:** Exactly one `<select>` (or date input) controls the global as-of date; no additional date state is introduced.
**Pass criteria:** DOM contains exactly one date selector; seed source and J-38 fix add zero date-picker elements.

---

### TC-18 — Fixture DB Does Not Mutate Committed Seed

**Type:** artifact
**Preconditions:** Backend running; fixture DB has been built and used for tests.

**Steps:**
1. Verify the fixture DB is located at a temporary/throwaway path (e.g. `/tmp/...` or `runs/...`), NOT at `apps/backend/data/trendora.db` or `apps/backend/data/seed/`.
2. Inspect the committed `apps/backend/data/seed/` directory and verify all files are unchanged (git status shows no modifications).

**Expected outcome:** Fixture DB is isolated to a temporary location; committed seed data is untouched.
**Pass criteria:** `git status apps/backend/data/seed/` shows no modifications; fixture DB path is not under `apps/backend/data/`.

---

### TC-19 — Backend Full Test Suite Green

**Type:** api
**Preconditions:** All backend code changes are complete; backend environment is set up.

**Steps:**
1. Run `pytest apps/backend/tests/ -v` (or the equivalent test command from `.claude/project-template.md`).
2. Capture the full output (stdout + stderr).
3. Verify exit code is 0 (all tests passed).

**Expected outcome:** All tests pass; no regressions; no skipped tests unless explicitly expected.
**Pass criteria:** Exit code is 0; test count matches the baseline (or increases if new tests were added); no failed assertions.

---

### TC-20 — Key-Leak Regression: Session Key Absent From Error Path (J-33 Critical)

**Type:** api
**Preconditions:** Backend running; fixture DB loaded; a pull/retry/resume operation over a needs-key provider is executed with a session key.

**Steps:**
1. Execute a pull or retry job with a real (or test) session key.
2. If the job encounters an error (e.g. invalid key format), inspect the error response and the job card.
3. Use `GET /api/data/jobs/{id}` to fetch the job details.
4. Grep the entire JSON response for the session key, `?token=`, `?apikey=`, or URL-encoded variants.
5. Verify the key is NOT present in any field of the response.
6. Repeat for a Resume operation that fails with 400.

**Expected outcome:** Session key is never leaked into the job card, error message, or logs; only the provider label and type are visible.
**Pass criteria:** Session key is completely absent; test key is not echoed back; httpx error string does not embed the URL with the key.

---

## Summary

**Total test cases:** 20
- **API tests:** 6 (TC-01, TC-02, TC-03, TC-04, TC-06, TC-16, TC-19, TC-20)
- **Browser tests:** 12 (TC-05, TC-07, TC-08, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-17, TC-18, TC-20 cross-type)
- **Artifact checks:** 2 (TC-18, TC-19)

**Critical focus areas:**
1. **J-37 (diagnostic + pull):** three-category render, gap-exact request body, completion, coverage update, error handling
2. **J-38 (resume + error fix):** successful resume from checkpoint, needs-key-without-key shows inline error and retains row, key not leaked, retry/dismiss preserve audit
3. **J-39 (remove + preview):** non-destructive preview on live host, wholly-seed refusal, destructive confirm and cascade on fixture
4. **J-35 (expand):** end-to-end seed-source expand, grown universe count, omitted-with-reason, non-cap-provider gate
5. **Regression safeguards:** J-18 (one date selector), J-33 (key leak), fixture isolation, full test suite green
