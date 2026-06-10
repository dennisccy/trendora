# goal-i_can_see_the_wealthy_future_forever-iter-27 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-27
**Date:** 2026-06-09
**Frontend Present:** yes

## Phase Goal

Capture the four remaining Data-Manager Must-have journeys (J-37, J-38, J-39, J-35) end-to-end against a fixture DB with the env-gated offline `seed` import source enabled. Convert them from `partial` to `passing` by demonstrating: missing-data diagnostic with gap-exact pull, successful Resume from checkpoint, seed-safe Remove confirm-preview, and Expand-universe with passers/omitted/grown-count.

## Test Cases

### TC-01 — J-37: Missing-data diagnostic renders all three categories with exact shortfalls

**Type:** browser
**Preconditions:** Fixture DB booted with three env values from `build_qa_fixture_db.py`; backend running at :8835 with `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1`; frontend running at :3000; global as-of control resolved; "Checking backend…" health badge cleared.

**Steps:**
1. Navigate to `http://localhost:3000/data` (Data Manager).
2. Locate the Missing-data diagnostic panel.
3. Observe the three diagnostic categories: "No history" (ANET), "Thin coverage" (DELL), and "Intra-series gaps" (MU).
4. For each row, verify the shortfall is enumerated (start/end dates and gap description).

**Expected outcome:** The three categories render with exact symbol/date shortfalls matching the fixture's insufficient members (no fabricated row; honest state).
**Pass criteria:** All three categories visible with distinct symbols and date ranges; shortfalls match the expected fixture gaps (ANET: no history; DELL: thin; MU: intra-series gap).

---

### TC-02 — J-37: Gap-exact pull completes and clears the diagnostic row

**Type:** browser
**Preconditions:** TC-01 passed; diagnostic panel visible with three rows; "seed" import source present in the Import source picker.

**Steps:**
1. On the "No history" (ANET) diagnostic row, click **"Pull the missing data"**.
2. Monitor the import job status (check `/api/data/jobs/{id}` in Network tab).
3. Wait for the pull job to complete (status `completed`, no errors).
4. Verify the job's `symbols` + `[start, end]` scope equals the diagnosed gap (NOT the whole universe/window).
5. On job completion, observe the diagnostic row clears and Coverage (J-36) updates to reflect ANET is now covered.

**Expected outcome:** The gap-exact pull job runs successfully over the `seed` source, fetching only the diagnosed shortfall. The diagnostic row clears, and coverage expands.
**Pass criteria:** Job completes with `symbols=['ANET']` and a `[start, end]` matching the diagnosed no-history gap; diagnostic row gone; Coverage now includes ANET with honest bar count; no fabricated bar (real seed data only).

---

### TC-03 — J-38: Seeded resumable checkpoint Resumes successfully from next_chunk_index

**Type:** browser
**Preconditions:** Fixture DB booted; Unfinished-imports panel on `/data` visible; a `seed`-source resumable checkpoint seeded in the fixture (intentionally paused mid-import).

**Steps:**
1. Take a screenshot showing the Unfinished-imports panel with the resumable checkpoint (e.g. job displaying `next_chunk_index: 2` or similar state).
2. Click **"Resume"** on the resumable job.
3. Monitor the job status on `/api/data/jobs/{id}` (Network tab) until completion.
4. Verify the job `next_chunk_index` advanced (distinct from the pre-Resume value).
5. Take a second screenshot after Resume completes; verify the row is cleared and job status is `completed`.

**Expected outcome:** Resume continues from the last completed chunk, advances the checkpoint, and completes successfully.
**Pass criteria:** Two distinct sha256-deduped screenshots showing the before (resumable state with visible `next_chunk_index`) and after (row cleared, job completed); checkpoint advanced; no stale/error state.

---

### TC-04 — J-38: needs-key Resume without key shows visible inline error and retains the row

**Type:** browser
**Preconditions:** Fixture DB booted; a resumable checkpoint requiring an API key (e.g. Alpha Vantage key) seeded in the fixture; Unfinished-imports panel visible.

**Steps:**
1. Verify the Unfinished-imports panel shows the resumable job requiring a key (job source = "alpha_vantage" or similar).
2. Click **"Resume"** without providing a key (or with no key in the session).
3. Monitor the job status in Network; expect a 400 error from the backend.
4. Observe the inline error alert on the job row (`role="alert" data-testid="resume-error"`).
5. Verify the row is **not silently dropped** — it remains visible with the error state.

**Expected outcome:** Resume without a key returns 400; a visible inline error renders; the row is retained (not deleted or hidden).
**Pass criteria:** Inline error alert visible on the row; job card shows error state; row persists in the Unfinished-imports panel (not silently removed); the error string is key-scrubbed (no `?token=` or `?apikey=` in the backend response or `/api/data/jobs/{id}` response).

---

### TC-05 — J-39: Remove-data confirm-preview enumerates removable bars and protected seed

**Type:** browser
**Preconditions:** Fixture DB booted; `/data` page visible; a user-added bar (not part of the committed seed) and seed bars for the same symbol exist.

**Steps:**
1. Locate the Remove-data form (bottom of the Coverage section).
2. Select a symbol that has both user-added and seed bars (e.g. ANET with 2 user-added bars beyond the seed).
3. Click **"Preview"** (non-destructive preview on the live host).
4. Observe the confirm-preview breakdown showing:
   - User-added bars (count, date range, "Removable")
   - Committed seed bars (count, "Protected — part of the seed")
   - Dependent cascade (snapshots and forward-returns derived from the user-added bars only)

**Expected outcome:** Preview enumerates exactly what will be removed (user-added bars + range) and what is protected (committed seed), with cascade breakdown.
**Pass criteria:** Preview shows removable count matching the user-added bars; seed bars flagged as "Protected"; cascade count accurate; the preview is honest and detailed (not vague).

---

### TC-06 — J-39: wholly-seed Remove scope is refused with explicit reason

**Type:** browser
**Preconditions:** Fixture DB booted; `/data` page visible; a symbol with only seed bars (no user additions) available.

**Steps:**
1. On the Remove-data form, select a symbol that contains ONLY committed seed bars (e.g. pure seed NVDA or test symbol).
2. Click **"Preview"**.
3. Observe the refusal message.

**Expected outcome:** The preview is refused with an explicit reason (e.g. "All bars are part of the committed seed and cannot be removed").
**Pass criteria:** Refusal message is clear and specific; no preview generated; no attempt to cascade-delete is made.

---

### TC-07 — J-39: destructive confirm and whole-row cascade on fixture DB only

**Type:** browser
**Preconditions:** Fixture DB booted; a confirm-preview for a user-added-only or mixed symbol ready (TC-05 passed).

**Steps:**
1. (Only on the fixture DB — never on the live host.) On the confirm-preview for a symbol with user-added bars, click **"Confirm Delete"**.
2. Monitor the backend job status `/api/data/jobs/{id}`.
3. Wait for the job to complete.
4. Verify the cascaded snapshots and forward-returns are removed (whole-row deletion, not in-place mutation).
5. Check Coverage to confirm the symbol is no longer listed (if wholly removed) or updated (if some seed bars remain).

**Expected outcome:** Destructive confirm deletes user-added bars and cascades the dependent snapshots/forward-returns (whole-row deletion). Seed bars are never affected.
**Pass criteria:** Job completes successfully; removed snapshots/forward-returns confirmed gone via `/api/data` response; Coverage reflects the removal; no in-place overwrite/mutation; no attempt to re-compute old snapshots.

---

### TC-08 — J-35: Seed-source Expand runs end-to-end to passers + omitted-with-reason + grown count

**Type:** browser
**Preconditions:** Fixture DB booted; `/data` page visible; Import source picker shows "seed" source available.

**Steps:**
1. Navigate to the Import source picker (on the Data Manager page).
2. Select the **"seed"** import source.
3. Click **"Expand universe"** (or equivalent control).
4. Monitor the expand job status until completion.
5. Observe the result panel showing:
   - List of symbols that passed the screen (passers)
   - List of symbols omitted with reason (omitted-with-reason)
   - Grown universe count (new total count vs. previous)
6. Verify the grown count matches `/api/methodology` resolved size and `/api/data` `universe_count`.

**Expected outcome:** Expand runs end-to-end; result panel displays passers, omitted-with-reason, and grown universe count accurately.
**Pass criteria:** Result panel visible; passers list present; omitted-with-reason list with reasons shown; grown count matches `/api/methodology` universe size (confirmed via API assertion); all values read from canonical producers (not fabricated).

---

### TC-09 — J-18: Exactly one global date selector; seed/expand/pull/resume controls add zero new date state

**Type:** browser
**Preconditions:** TC-02, TC-03, TC-05, TC-08 passing; Data Manager page visible with all four flows demonstrated.

**Steps:**
1. With DevTools open, run: `document.querySelectorAll('select, input[type=date]').length` in the console.
2. Verify only ONE `<select>` element exists (the global as-of control).
3. Inspect the page for any hidden or conditional date pickers introduced by the seed source, expand, pull, or resume flows.
4. Check the job-status responses and the job card DOM for any `as_of` / date parameter that is NOT a job-metadata field.

**Expected outcome:** Exactly one date control on the page; job/action date inputs are parameters, not a second date control.
**Pass criteria:** DOM query returns 1; no second date picker exists (even hidden/conditional); all four flows read the single global as-of control.

---

### TC-10 — J-33: Key-leak scrub on pull/retry/resume/expand error strings

**Type:** browser
**Preconditions:** TC-02, TC-03, TC-04 passed; any error state captured (e.g. needs-key Resume 400).

**Steps:**
1. For each error returned in TC-02 (pull), TC-03 (resume success — no error expected), TC-04 (resume 400), and TC-08 (expand — if any error):
   - Check the job-status response (`GET /api/data/jobs/{id}`) `errors[]` field.
   - Check the job card DOM for displayed error text.
   - Grep the run history for any logged error.
2. Verify no error string contains `?token=`, `?apikey=`, or any bearer token / API key.

**Expected outcome:** All error strings are scrubbed; sensitive keys do not appear in responses, DOM, or logs.
**Pass criteria:** Sentinel + redacted key (e.g. `?token=***` or omitted entirely) in all error contexts; no raw key leaked (real httpx assertion on the backend response).

---

### TC-11 — Required-still-passing: J-17, J-34, J-36, J-08 remain green

**Type:** browser
**Preconditions:** Fixture DB booted; all four target journeys captured (TC-01–TC-08).

**Steps:**
1. Confirm J-17: existing fetch/backfill/both path intact — no second fetch path introduced.
2. Confirm J-34: Resume/Retry/Dismiss job-control endpoint works as before (no second resume path).
3. Confirm J-36: Coverage updates correctly after pull/remove (values match audit trail).
4. Confirm J-08: Dismiss/Remove drops only job-control record; immutable scanner snapshot and forward-return rows are preserved.

**Expected outcome:** All four journeys behave as before; the pull/resume/remove/expand flows use the existing canonical paths.
**Pass criteria:** J-17 fetch path unchanged; J-34 resume endpoint unchanged; J-36 coverage accurate; J-08 dismissal drops job-control only (audit + snapshot rows intact).

---

### TC-12 — Required-still-passing: J-06, J-07, J-15 (scoring/snapshot unchanged, no DB regen)

**Type:** artifact
**Preconditions:** iter-27 diff available; fixture DB populated.

**Steps:**
1. Run `cd apps/backend && git diff HEAD -- apps/backend/app/engine/` | grep -E 'scanner|scoring|snapshot|regime|pattern'` — confirm zero changes.
2. Run the backend suite once: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (full suite ~14 min; run ONCE).
3. Verify no new test failures vs iter-26 baseline.

**Expected outcome:** Scoring/snapshot path git-untouched; suite passes; byte-identical snapshots (no DB regen).
**Pass criteria:** Diff shows no changes to scoring/scanner/snapshot engines; pytest exits 0; test counts match baseline.

---

### TC-13 — Environment and harness wiring (gates all other tests)

**Type:** artifact
**Preconditions:** Fresh terminal; no lingering backend/frontend processes.

**Steps:**
1. Stop any lingering servers by port: `lsof -i :8835,8836,3000,3001,3835` and kill by PID (never broad `pkill -f`).
2. Run `rm -rf apps/frontend/.next` to clear the dead-shell cache.
3. Run `cd apps/backend && .venv/bin/python scripts/build_qa_fixture_db.py` and capture the final JSON line.
4. Extract and export the three env values from the JSON: `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1`, `TRENDORA_CONFIG=<path>`, `TRENDORA_SEED_IMPORT_DIR=<path>`.
5. Boot the backend with the three env values: `TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1 TRENDORA_CONFIG=<path> TRENDORA_SEED_IMPORT_DIR=<path> uvicorn ...`.
6. Boot the frontend: `cd apps/frontend && npm run dev`.
7. Verify `http://localhost:3000/_next/static/chunks/main-app.js` returns 200.
8. Verify the "Checking backend…" health badge on `/data` or `/stocks` is cleared (backend reachable).
9. Assert the **"seed" import source is present in the picker** on `/data` (its absence means env flag did not reach the backend).

**Expected outcome:** Fixture DB built; three env values exported; both servers booted with the fixture config; frontend hydrated; seed source visible in the picker.
**Pass criteria:** Fixture build exits 0; servers boot without error; health badge cleared; "seed" source listed in the Import source picker on `/data`.

---

## Summary

**Total test cases: 13**
- **Browser tests:** 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-08, TC-09, TC-10, TC-11)
- **Artifact checks:** 4 (TC-07, TC-12, TC-13)
- **API tests:** 0 (all flow validation via browser; error scrub via job-status response inspection)

**Defining tests (all must capture green for iter-27 PASS):**
- **TC-02** — J-37 gap-exact pull: diagnostic row clears, coverage updates
- **TC-03** — J-38 Resume success: checkpoint advances, distinct before/after sha
- **TC-04** — J-38 needs-key error: visible inline alert, row retained
- **TC-08** — J-35 Expand: passers/omitted/grown-count; universe size matches `/api/methodology`

**Principal-risk tests:**
- **TC-09** — J-18: exactly one date selector (anti-goal watch)
- **TC-10** — J-33: key-leak scrub on all error paths (MEMORY `httpx-error-leaks-url-query-key`)
- **TC-13** — Environment wiring: seed source present, fixture DB booted (the iter-23/24/25/26 recurrence gate)

**Required-still-passing guard:** TC-11, TC-12 (J-17, J-34, J-36, J-08, J-06, J-07, J-15 unchanged).
