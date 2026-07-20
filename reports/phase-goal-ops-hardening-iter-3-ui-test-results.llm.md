# Phase goal-ops-hardening-iter-3 — UI Test Results

**Phase:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL because: UT-02 (happy-path, P1, THE target journey for this iteration / J-05) did not verify
     its literal expected result, and UT-06 (regression, P1) reproducibly failed — a job-progress
     heartbeat freeze the frontend itself surfaces as "· possibly stalled". Per the agent's own rule,
     any P1/happy-path failure forces FAIL. See detailed writeups below: both failures are backed by
     strong, precise evidence, and important exculpatory/contextual detail is included for each so the
     next stage (auditor / goal-evaluator) can weigh severity and root-cause attribution accurately. -->

**Overall:** 8/11 test rows passed, 2 failed, 1 skipped

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads with coverage panel visible | smoke | P1 | Heading, subtitle, all 7 stat tiles populated, both panels visible, no error card | All present exactly as specified; Universe 540, Symbols 591, Trading days 5380, Snapshot dates 762, Backfill gaps 4618 all non-blank | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-01-result.png` |
| UT-02 | Fetch lands new bar -> coverage refreshes + persists after reload | happy-path | P1 | Job settles ok/partial; coverage panel auto-updates with Symbols/Trading days/Snapshot dates higher; same numbers survive hard reload; never false all-zero | Job settled ("partial") both times tried; NONE of Symbols/Trading days/Snapshot dates increased (see Failed Tests); Price History end-date DID advance and DID persist after reload, proving the underlying storage-refresh mechanism fires, but the test's specific named fields did not move | FAIL | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-02-coverage-after-reload.png` |
| UT-03 | Repeat fetch is a fast, silent no-op | regression | P1 | 2nd run no slower than 1st; coverage numbers identical; normal terminal status, nothing new | Run1 12.98s, Run2 8.49s (2nd faster, not slower); all 6 tracked coverage fields byte-identical before/after; both settled "partial" (steps text explicitly allows partial as a settle state) with the same stable 429 ok/162 failed split both times | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-03-repeat-fetch-noop.png` |
| UT-04 | Fresh DB boot shows honest all-zero coverage | regression | P1 | All-zero coverage on very first request against a never-ingested DB | Not executed — see Skipped Tests | SKIP | none |
| UT-05 | Multi-day backfill still renders breakdown + updates coverage | regression | P1 | Breakdown line with real numbers, chunk badge if applicable, Snapshot dates up / Backfill gaps down by the right amount | "8 calendar days . 1 already snapshotted . 2 non-trading" rendered; chunk 1/1 (range too small to need chunking, correctly omitted); Snapshot dates 762->767 (+5), Backfill gaps 4618->4613 (-5), exact match to snapshots_created=5 | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-05-backfill-breakdown.png` |
| UT-06 | Backend stays "Ready", job panel keeps ticking during heavy job | regression | P1 | Header badge stays "Ready" throughout; heartbeat/activity line keeps advancing, never freezes or shows "possibly stalled"; ends "ok" | Header badge DID stay "Ready" throughout (confirmed) BUT the Job progress panel's heartbeat froze for ~260-270s (of ~316-327s total) after the per-date scan finished, and the UI visibly showed "updated 33s ago . possibly stalled" live in the browser; reproduced twice | FAIL | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-06-possibly-stalled.png` |
| UT-07 | Malformed date blocks submit with inline error | validation | P2 | Red inline "Enter a valid date..." message + triangle icon, red border, Start disabled | All confirmed via DOM inspection: `aria-invalid="true"`, `border-neg` class, `lucide-triangle-alert` svg, exact message text, `btnDisabled: true` | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-07-invalid-date.png` |
| UT-08 | Backend-unavailable shows honest error card | error | P2 | Warning-triangle card, bold "Backend unavailable", exact explanatory text below, no coverage numbers shown | Backend killed; page rendered exactly: "Backend unavailable" / "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." with AlertTriangle icon (confirmed in source); zero coverage numbers rendered | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-08-backend-unavailable-card.png` |
| UT-09 | "Refreshed:" line absent for fetch, present for backfill | regression | P2 | Fetch run/row: no "Refreshed:" line despite coverage updating; backfill run/row: "Refreshed: coverage, ..." present | Every fetch job this session showed `aggregates_refreshed: []` (API) and no "Refreshed:" text anywhere in its Run-history entry; every backfill job showed a populated `aggregates_refreshed` list including "coverage" and the matching UI line, e.g. "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" | PASS | see UT-02/UT-05 evidence + inline JSON in this report |
| UT-10 | "Job kind" dropdown is clear and form adapts | ux | P3 | 3 plain-worded options, Import source shown only for Fetch/Fetch+backfill, no layout breakage | Options exactly "Backfill snapshots" / "Fetch EOD prices" / "Fetch + backfill" (no raw codes); Import source select appears (2 selects) for both fetch kinds and disappears (1 select) for Backfill snapshots; no visual breakage across all 3 states | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/UT-10-fetch-backfill-form.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (regression journey, executed per goal.md) | regression | P1 | Restart->first-200 <=5s; a pre-ready payload carries boot phase + progress n/m; kill->explicit crashed presentation distinct from initializing; logfile has boot events and ends abruptly after a kill; restart->mid-flight job shows explicit "interrupted" state, never still-"running" | All 6 steps confirmed directly: first 200 at 1.49s; captured "initializing" + "history 89/89" + status="running" for a real ~2s pre-ready window; killed backend -> badge "Backend unavailable" + banner "Backend is unavailable — the preflight check could not run." (distinct wording from the initializing/servability-gap case); logfile's fresh boot marker present, prior lines end on a plain request log with no shutdown line; restarted -> the killed job (id 65, 2012-01-01->2013-12-31) now shows `"status": "interrupted"` with its last real persisted progress (0/0, honestly reflecting how little it had done) in Run history | PASS | `reports/qa/goal-ops-hardening-iter-3-evidence/J-04-crashed-badge.png` |

---

## Passed Tests

### UT-01 — `/data` loads with coverage panel visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-01-result.png`
- "Data Manager" heading and the subtitle beginning "Grow the dataset on demand..." both visible.
- All seven stat tiles show real values: Price history 1996-01-02 -> 2026-07-17, Universe 540, Candidate universe 122, Symbols 591, Trading days 5380, Snapshot dates 762, Backfill gaps 4618.
- "Start a fetch / backfill job" and "Job progress" panels both visible; no "Backend unavailable" card; no blank/crashed page.

### UT-03 — Repeat fetch is a fast, silent no-op
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-03-repeat-fetch-noop.png`
- Submitted "Fetch EOD prices" (2005-02-28 -> 2005-03-07) twice back to back. Run 1: 12.98s wall time, settled "partial" (429/591 ok, 162 failed, 0 new bars — this exact range had already been exercised earlier in the session, so it was itself already a no-op run). Run 2 (immediate identical resubmit): 8.49s — faster, not slower.
- Coverage fields checked byte-for-byte via `GET /api/data` before/after Run 2: `price_start`, `price_end`, `symbol_count`, `trading_day_count`, `snapshot_count`, `gap_count` — all six identical.
- No error; the same stable partial split (429 ok/162 failed) both times indicates deterministic, non-flaky behavior. The test's own Steps text explicitly allows "ok (or partial)" as the settle state, so "partial" here satisfies "normal terminal status."

### UT-05 — Multi-day backfill still renders breakdown + updates coverage
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-05-backfill-breakdown.png`
- Backfill 2005-02-28 -> 2005-03-07 (the page's own default-prefilled range for this kind). Job settled "ok".
- Breakdown line rendered with real numbers: "8 calendar days · 1 already snapshotted · 2 non-trading" (8 calendar days = 6 trading + 2 non-trading, matches `dates_total=6`/`non_trading_days=2`/`calendar_days=8` from the API).
- Chunk badge correctly omitted (chunk_index=1/chunk_total=1 — range too small to need chunking; the test only requires the badge "if the range is large enough").
- Coverage: Snapshot dates 762 -> 767 (+5, exactly `snapshots_created`), Backfill gaps 4618 -> 4613 (-5). `gap_first` advanced from 2005-02-28 to 2005-03-08 (the next real gap). "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" line present.

### UT-07 — Malformed date blocks submit with inline error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-07-invalid-date.png`
- Typed `2026-13-40` into Start date. Confirmed via DOM: input gets `border-neg` class (red border) and `aria-invalid="true"`; an adjacent `<span role="alert" data-testid="job-start-date-error">` contains a `lucide-triangle-alert` SVG plus the exact text "Enter a valid date as yyyy-MM-dd", positioned directly below the field (same `flex flex-col` label).
- The Start submit button's `disabled` property is `true` while the invalid value is present.

### UT-08 — Backend-unavailable shows honest error card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-08-backend-unavailable-card.png`
- Stopped the backend (`kill -9` on the uvicorn process) and reloaded `/data`.
- Page rendered a small, sane DOM (no crash, no blank screen, no stack trace, no generic browser network-error page) containing, verbatim: bold "Backend unavailable" followed by "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." — an exact match to the test's expected text. Confirmed in source (`apps/frontend/app/data/page.tsx:461-468`) that this card also renders a Lucide `AlertTriangle` icon.
- Zero coverage numbers were rendered anywhere on the page (no fabricated "0").

### UT-09 — "Refreshed:" line absent for fetch, present for backfill
**Verdict:** PASS
**Evidence:** Cross-referenced from UT-02/UT-03 (fetch runs) and UT-05 (backfill run) API captures above.
- Every fetch-kind job run this session (4 of them, spanning both the 2005 default range and the forward-dated 2026-07-18->07-20 range) returned `"aggregates_refreshed": []` from `GET /api/data/jobs/{id}`, and none of their Run-history entries show any "Refreshed:" text — only the plain "N/N symbols ok" summary — even though (per UT-02) the coverage numbers themselves did silently update.
- Every backfill-kind job run this session returned a populated `aggregates_refreshed` array (e.g. `["latest_snapshot","coverage","membership_timeline","market_phase","research_hot_keys"]`) and the UI correctly showed "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" (or the shorter "Refreshed: coverage, membership timeline, research hot keys" for a run with no newly-created snapshot dates) on both the live job card and the persisted Run-history row.

### UT-10 — "Job kind" dropdown is clear and form adapts
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-10-fetch-backfill-form.png`
- Dropdown options, read via DOM: exactly "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill" — no raw internal codes shown.
- Selecting "Fetch + backfill" (value `both`) or "Fetch EOD prices" (value `fetch`) reveals a second "Import source" select (confirmed: 2 selects present, `sourceValue: "yahoo"`, label text "Import source" + "Yahoo Finance · a[vailable]"). Selecting "Backfill snapshots" hides it again (back to 1 select). Cycled through all three states; no layout breakage or leftover fields observed in either the DOM counts or the screenshots.

### UT-J-04 — J-04: Non-blocking boot with visible status (regression journey)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/J-04-crashed-badge.png`

Executed per goal.md's own numbered steps, using a real backend process this run controls (PID discovered via `ps`, restarted via `scripts/start-backend.sh`, never `dev.sh`):

1. **Restart -> first `GET /api/health` 200 timing:** killed the live backend, relaunched via `scripts/start-backend.sh` in the background, and polled every ~0.2s from process launch. First 200 arrived at **1.49s** — well under the 5s budget.
2. Confirmed (same measurement as #1).
3. **Pre-ready payload carries boot phase + progress n/m:** with the frontend tab already open, polled `GET /api/health` at 0.25s intervals through a second restart. Captured **7 consecutive pre-ready responses** (spanning ~1.75s) with `"readiness": "initializing"` and `"warmup": {"done": 89, "total": 89, "status": "running", "message": "history 89/89"}` before it flipped to `"ready"` on poll 8. This is a real, well-formed "boot phase + progress n/m" payload, exactly as required. (The browser's own poll cadence happened to miss rendering a live screenshot of the ~2s "Initializing…" text this specific cycle — the transition window was short relative to the tab's poll interval — but the `HealthBadge` component's source (`components/health-badge.tsx:55-65`) directly confirms it renders "Initializing… history {done}/{total}" for this exact state, and the API-captured payload proves the state genuinely occurred.)
4. **Kill (simulated crash) -> explicit crashed presentation:** `kill -9`'d the backend mid-job. After the frontend's next poll cycle, the header badge flipped to **"Backend unavailable"** and the `PreflightBanner` showed **"NO-GO — do not rely on today's board." / "Backend is unavailable — the preflight check could not run."** — wording that is visibly distinct from the "Initializing…" presentation (never conflated with it).
5. **Logfile evidence:** `logs/backend.log` (persistent, append-only across restarts) contains a `=== start-backend.sh: launching at <ISO time> ===` marker for every boot this session, including this one. The lines immediately preceding the kill are ordinary `INFO: ... GET /api/data/jobs/... 200 OK` request logs with **no** "Shutting down" / "Application shutdown complete" line — i.e. the log ends abruptly, exactly as a killed (not gracefully stopped) process would leave it.
6. **Restart -> mid-flight job shows "interrupted":** before killing the backend, a 2-year backfill (2012-01-01 -> 2013-12-31, run id 65) was started and was still running at the moment of the kill. After the restart, `GET /api/data`'s `runs` list shows that same run with **`"status": "interrupted"`** (not "running", and the live per-job polling endpoint now correctly 404s "unknown job" for its old in-memory id) with its last real persisted progress (`dates_done: 0`, `dates_total: 0`, `snapshots_created: 0` — honestly reflecting that it had barely started before being killed) rather than a phantom "still running with no living process" row.

All 6 steps hold. **No golden replay script was written for J-04** — see note at the end of this report.

---

## Failed Tests

### UT-02 — Fetch job that lands a new bar refreshes coverage in place, and the fix survives a reload
**Verdict:** FAIL
**Failure:** The Expected Result's core, specific assertion — "at least one of 'Symbols', 'Trading days', or 'Snapshot dates' is now a higher number than what was written down in step 2" — did not hold in either attempt made, including the test's own suggested contingency (widening the End date forward). This is the literal target-journey (J-05) acceptance step for this iteration's audit fix (B1).
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-02-coverage-after-reload.png`

**Steps taken:**
1. Baseline noted: Universe 540, Symbols 591, Trading days 5380, Snapshot dates 762, Price history 1996-01-02 -> 2026-07-17.
2. Attempt 1 (default pre-filled range, per literal test steps): Set kind "Fetch EOD prices", left the pre-filled Start/End (2005-02-28 -> 2005-03-07), clicked Start. Job settled "partial" (429/591 ok, 162 failed, **72 new bars**). Re-checked `GET /api/data`: Universe/Symbols/Trading days/Snapshot dates all **unchanged**. (These 72 new bars filled in-range gaps for symbols whose bars were already counted in the 591/5380/762 totals — they did not add a new symbol, a new trading day, or a new snapshot.)
3. Per the test's own contingency clause ("extend the End date... and repeat"), attempt 2: Start=2026-07-18, End=2026-07-20 (today, per the environment clock). Job settled "partial" (588/591 ok, 3 failed, **1 new bar**). Re-checked `GET /api/data`: `price_end` advanced from `2026-07-17` to `2026-07-20` (confirmed both via the live API and, separately, via a full page reload in the browser — the value persisted). **Symbols/Trading days/Snapshot dates still did not move.**
4. Root-caused precisely why (all via direct backend inspection, not speculation):
   - The single new bar landed for **`^VIX`**, not the benchmark. Direct DB query confirmed `SPY`'s own latest bar is still `2026-07-17`.
   - `apps/backend/app/engine/data_manager.py:143-150` (`_trading_days`) defines "Trading days" as strictly the **benchmark's** (SPY) own bar dates — so only a new SPY bar can move this figure. A direct single-symbol fetch of `SPY` for `2026-07-18 -> 2026-08-15` (a month beyond what was tried in the UI) returned **"1/1 symbols ok, 0 failed, 0 new bars"** — i.e. the real Yahoo Finance feed genuinely has no SPY data past `2026-07-17` at the moment this QA ran. This is an external, real-world data-timing ceiling, not a code path this iteration controls.
   - "Symbols" (`symbol_count`) can only increase if a symbol with **zero** stored bars gets its first one. The live `GET /api/data` diagnostic (`coverage.diagnostic`) shows `"no_history": []` and `"thin": []` — **there are currently no such symbols in this database** (every entry in the Missing-data diagnostic is an `intra_series_gap`, i.e. already has bars, already counted). There is categorically no fetch that can move Symbols right now.
   - "Snapshot dates" never changes via a `fetch`-kind job by design (only `backfill`/`both`/`rebuild` create snapshots) — confirmed both by source and by UT-09's evidence above.
5. Verified the underlying B1 mechanism separately, since the literal named-fields assertion was blocked by the above: `apps/backend/app/api/data.py:121-126` states in-source that `GET /api/data`'s `coverage` block is served **only** from the persisted `coverage_snapshot` row, "never a live `compute_coverage` call on this request path." Since `price_end` (part of that same served/stored payload) **did** advance immediately after the fetch and **did** survive a hard reload, this is direct proof the fetch's finalize hook correctly wrote a fresh row to storage — i.e. the B1 code path itself fired correctly; it is the three specific fields the test plan chose to track that happened to be un-movable in this environment at this moment.

**Expected:** After a fetch that lands a new bar, at least one of Symbols/Trading days/Snapshot dates increases, both live and after a hard reload.
**Actual:** None of the three increased in either attempt (fully explained above); Price History's end date did increase and did persist through a reload, evidencing the same underlying storage-write path.

**Note for the auditor/evaluator:** this is reported as FAIL because the literal, specified assertion did not verify — per this agent's instructions, alternative evidence should be surfaced, not used to silently upgrade a verdict. The exculpatory detail above is real and precise (external Yahoo data-timing ceiling for the benchmark; zero eligible zero-bar symbols exist right now; snapshot-count is fetch-independent by design) and should be weighed by whoever makes the next call on this journey's status. Separately (see "Additional Finding" below), performing this exact action also left the app-wide readiness badge reading "Backend unavailable" until a follow-up backfill was run for the new date — a related but distinct, pre-existing issue.

### UT-06 — Backend stays "Ready" and the job progress panel keeps ticking during a large job
**Verdict:** FAIL
**Failure:** The header readiness badge correctly stayed "Ready" throughout (that part of this test passes), but the **Job progress panel's own heartbeat/activity line froze for an extended period and the frontend visibly rendered "· possibly stalled"** — precisely the failure mode this test's Expected Result explicitly rules out.
**Evidence:** `reports/qa/goal-ops-hardening-iter-3-evidence/UT-06-possibly-stalled.png`

**Steps taken (reproduced twice, independently):**
1. Run A: Backfill `2010-01-01 -> 2010-06-30` (124 trading days, not previously backfilled). `started_at` 09:00:56.14, last `tick()`-driven progress update (`last_progress_at`) at 09:01:47.96 (~52s in, activity frozen at "scanning 2010-06-30 (124/124)"), `finished_at` 09:06:12.04 — **total 315.9s, of which ~264s (84%) had a frozen heartbeat** while `status` remained `"running"`.
2. Run B: Backfill `2011-01-01 -> 2011-06-30` (also 124 days). `started_at` 09:10:34.38, `last_progress_at` froze at 09:11:29.26 (~55s in), `finished_at` 09:16:01.53 — **total 327.1s, ~272s (83%) frozen**. This time watched live in the browser: at T+~33s past the freeze, the Job progress panel literally read **"updated 33s ago · possibly stalled"** (screenshotted) while `status` was still `"running"`.
3. Throughout both runs the **header** readiness badge (`data-testid="readiness-badge"`) stayed "Ready" the whole time — confirmed by direct checks during the stall window. The rest of the app kept responding to API calls (health/data polls) throughout, with no crash and no server-side slowdown observed.
4. Root-caused precisely: `JobProgress.tick()` (`apps/backend/app/engine/data_manager.py:1945-1952`) is the **only** method that stamps `last_progress_at`/`current_activity`, and it is called **per-date** inside the backfill scanning loop (`data_manager.py:2863`, `"scanning {date} ({n}/{total})"`). Once that loop finishes (124/124), the job moves into `_refresh_ingest_aggregates` (`data_manager.py:3034-3093`, invoked at `3790`) — which persists a fresh coverage snapshot (a real recompute, including the membership-timeline resolver), warms `market_phase_cached` for every one of the 124 newly-created dates in a loop, and warms one research hot-key — real, substantial work — but **contains zero `tick()` calls anywhere in the function**. `last_progress_at` therefore cannot advance during this entire phase. The frontend's own staleness check (`apps/frontend/app/data/page.tsx:2480-2501`) computes `stale = live && job.status === "running" && staleSecs > heartbeatStaleSeconds` and renders literally `" · possibly stalled"` when true; the configured threshold is `heartbeat_stale_seconds: 20.0` seconds (from `GET /api/data`'s `job_progress` block) — vastly exceeded by the observed ~264-272s untracked phase.

**Expected:** Heartbeat keeps advancing and the activity line keeps changing throughout; never freezes for an extended period; never shows "· possibly stalled".
**Actual:** Header badge behaved correctly, but the job-progress heartbeat froze for ~83-84% of total job duration in both independent runs, and the UI visibly displayed "· possibly stalled" for an extended, directly-observed period.

**Note for the auditor/evaluator:** this specific code path (`_refresh_ingest_aggregates`'s lack of `tick()` calls, and the whole per-date backfill loop it follows) is **not** part of this iteration's diff — B1/B2 only add a new `elif` branch for `fetch`/`expand` that calls the lighter `refresh_coverage_snapshot` directly (not the full `_refresh_ingest_aggregates`), which is presumably why the `fetch` jobs run during this same session (UT-02/UT-03) did not exhibit a comparable stall. This appears to be a **pre-existing** gap in the backfill/rebuild finalize path, surfaced here because this iteration's own regression plan called for exercising a genuinely heavy backfill. It directly affects the `required-still-passing J-04`/`J-05 step-4` acceptance this test exists to protect, so it is reported as a hard FAIL regardless of when it was introduced.

---

## Skipped Tests

### UT-04 — Fresh DB boot shows honest all-zero coverage
**Verdict:** SKIPPED
**Reason:** Requires restarting the backend against a genuinely fresh, never-ingested copy of the database — an environment-setup precondition this shared QA instance does not have (the one committed `apps/backend/data/trendora.db` here is already fully ingested, and there is no spare pristine copy to swap in without destroying the dataset every other test in this run — and the phase's own iteration state and future pipeline stages — depend on). The test plan itself flags this precondition as "not achievable by clicking alone in a normal shared instance," so this is an anticipated skip, not an oversight.

---

## Additional Finding (not a numbered test case, discovered during UT-02/UT-06 execution)

### FINDING — A bare "Fetch EOD prices" that lands a bar for a date newer than the latest snapshot flips the app-wide readiness badge to "Backend unavailable"

While executing UT-02's forward-dated fetch (landing the `^VIX` bar for `2026-07-20`), the header readiness badge and the `PreflightBanner` flipped to **"Backend unavailable"** / **"NO-GO — do not rely on today's board."** app-wide, even though the backend was fully up, healthy, and serving every request normally. Root-caused via direct source read:

- `apps/backend/app/engine/readiness.py:127-129`: `latest_servable = bool(latest_data is not None and latest_run is not None and latest_run >= latest_data)`. `latest_data` (`apps/backend/app/engine/prices.py:50-53`, `latest_data_date`) is `max(DailyPrice.date)` over **all** symbols, while `latest_run` is the newest **snapshot** date. A fetch that lands even a single bar for any one symbol on a date newer than the latest snapshot makes this condition false, and `compute_readiness` returns `state = "unavailable"` — the exact same state value a genuine crash produces (`apps/frontend/components/health-badge.tsx:66-74` renders it identically as "Backend unavailable" either way; only the `PreflightBanner`'s longer reason text differs: "No servable snapshot: the database is unreachable or no run is persisted for the latest data date." for this case vs. "Backend is unavailable — the preflight check could not run." for an actual connection failure — confirmed by directly observing both).
- Worse: the date this created (`2026-07-20`, `^VIX`-only) turned out to be **un-backfillable** through the normal UI, because `_trading_days` (`data_manager.py:143-150`) defines the trading calendar as the **benchmark's** (SPY) own bar dates only — and SPY has no bar for that date. A "Backfill snapshots" job for exactly that date correctly reported "0 snapshots over 0 dates" (an honest non-trading-day read, since the benchmark doesn't recognize the date), so there was **no ordinary in-app action that could clear the condition**. The only working remedy was the "Remove imported data" by-date-range feature (`apps/frontend/app/data/page.tsx:3208+`) — used here to delete the single stray bar and restore `latest_run >= latest_data`, after which readiness correctly returned to "ready".
- This logic is **pre-existing** (not part of this iteration's `data_manager.py` diff, which only touches the `coverage_snapshot` refresh trigger, not `app.engine.readiness`) — but it is directly, easily triggered by this exact iteration's own celebrated, newly-fixed scenario (an ordinary, standalone "Fetch EOD prices" click), and left the app in a state with no obvious in-app fix. Recommend a future iteration either (a) exclude dates the benchmark hasn't reached yet from the `latest_servable` comparison (compare against the benchmark's own latest bar, not any symbol's), or (b) give the header/banner a distinct, less alarming label for "new data landed, snapshot pending" versus a genuine unreachable backend.

Evidence: `reports/qa/goal-ops-hardening-iter-3-evidence/FINDING-backend-unavailable-badge.png`.

---

## Golden Replay Scripts

No new golden replay script was written this run.

- **J-01, J-03:** out of scope this run per the dispatch instructions (already re-verified via stored golden scripts; not re-tested).
- **J-05 (UT-02):** deliberately **not** written. A deterministic replay script would need to reliably reproduce "a fetch lands a new bar that moves Symbols/Trading days/Snapshot dates" — but this run just demonstrated that outcome depends on live, real-world Yahoo Finance data availability for the specific benchmark symbol and date range, which is not reproducible on demand and would make the script flaky-by-construction (a future replay could easily fail for reasons having nothing to do with the product). Best-effort skip per the agent instructions.
- **J-04:** deliberately **not** written. J-04's acceptance is fundamentally about backend process lifecycle (restart timing, `kill -9` crash detection, logfile inspection, mid-flight-job interruption) — none of which is expressible in the replay runner's `goto`/`click`/`fill` action vocabulary (there is no "kill the backend process" action). A script that only checked something trivial like "the page loads and shows Ready" would not actually exercise anything specific to J-04 and would risk giving false confidence in a future fast-replay lane. Skipped rather than produced a misleading stand-in.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health: `/api/health`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-20
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-3-evidence/`
- **Backend restarts performed:** 3 (two deliberate `kill -9` + `scripts/start-backend.sh` relaunch cycles for J-04/UT-08, restored to a clean, fully "Ready" state afterward each time — confirmed by a final post-test check: readiness `ready`, `/data` rendering normally, Price history back to `1996-01-02 -> 2026-07-17`).
- **Residual environment state from testing:** the committed database now has additional backfilled ranges (2005-02-28→2005-03-07, 2010, 2011, plus the pre-existing 2025-06-01→2026-07-17) and a `DEGRADED` (not `GO`) preflight verdict from an honest, non-blocking "drift" signal — live Yahoo Finance data for a few historical dates fetched during this session differs slightly (an adjustment seam) from the originally committed seed. This is expected, descriptive-only, non-fabricated, and does not affect `readiness` (still "ready").
