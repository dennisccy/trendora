# goal-ops-hardening-iter-0 — UI Test Results

**Phase:** goal-ops-hardening-iter-0 (baseline — verify-only, no code changes)
**Date:** 2026-07-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- This is the expected/intended outcome of a baseline iteration whose entire purpose is to honestly
     record which of the five ops-hardening journeys already pass against the current codebase, per the
     iter spec's own framing ("record for each whether it already passes, fails, or is partial — with no
     code changes"). A FAIL verdict here is a measurement, not an incident. -->

**Overall:** 0/5 journeys passed cleanly, 1 partial (scored FAIL per the strict PASS/FAIL/SKIP contract —
see its row), 4 failed, 0 skipped.

All five journeys were exercised live against the running app (backend :8255 started via
`scripts/start-backend.sh`, frontend :3255 via `scripts/start-frontend.sh` — prod mode, matching J-04/J-06's
own measurement conditions) using Chrome MCP for every UI-observable step, corroborated with direct
API/DB/source inspection where the journey's own steps require backend restarts, process kills, or log/DB
state that a browser cannot observe. Every FAIL below is a live, reproduced finding (not a code-read
hypothesis) — mostly confirming, with fresh empirical evidence, what the developer step's preliminary
code-level pass (`docs/handoffs/goal-ops-hardening-iter-0-dev.md`) had already hypothesized.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors requested range and explains zero-work | happy-path | P1 | Explicit May 2026-05-02→05-29 backfill produces `dates_total=19`, creates snapshots for in-range dates, a weekend-only run and a re-run explain their zero-work with a per-date reason breakdown, all three runs persist across reload, and zero-work renders visually distinct from success | Live backfill of the exact range returned `dates_total=0` / 0 snapshots (cadence gate still filters explicit requests); `/scanner-runs` shows only the pre-existing 2026-05-01, no new dates; weekend-only and re-run both show the same generic "0 snapshots over 0 dates" text with no reason breakdown; the ephemeral "Job progress" panel resets to "No job has been started this session" on reload (the literal forbidden phrase); the persisted "Run history" table does survive reload but shows every zero-work AND every productive run with the identical `ok` status badge — no visual distinction | FAIL | `reports/qa/goal-ops-hardening-iter-0-evidence/J-01-may-backfill-zero-dates.png`, `J-01-J-05-data-page-fullpage.png`, `J-01-data-initial.png` |
| UT-J-03 | No per-run range cap | happy-path | P1 | A backfill spanning >370 calendar days (2025-06-01→2026-07-17, 412 days) is accepted with no rejection and executes in visible chunks | Live submission returned the literal inline error "date range too large: 412 days exceeds the configured maximum 370" — request rejected client-side by the form, no job created, `config.yaml`'s `max_range_days: 370` and its enforcement in `data_manager.py` are unchanged | FAIL | `reports/qa/goal-ops-hardening-iter-0-evidence/J-03-submit-attempt.png` |
| UT-J-04 | Non-blocking boot with visible status | happy-path | P1 | First `/api/health` 200 ≤5s of process start; pre-ready responses/badge show boot phase+progress (never bare "unavailable"); kill shows a distinct crashed presentation; a persistent backend logfile shows boot events and ends abruptly on crash; a mid-flight job shows "interrupted" after restart, never stuck "running" | 5/6 sub-checks PASSED live: first 200 at 0.909s and 1.05s across two independent restarts (well under 5s); badge showed "Initializing… history 89/89" during a genuine ~13s pre-ready window; badge showed "Backend unavailable" (red) plus preflight NO-GO banner immediately after a simulated `kill -9`; a job killed mid-flight (`status=running`) came back `status=interrupted` in both the DB and the `/data` Run history table after restart. ONE confirmed FAIL: no persistent backend logfile exists — `scripts/start-backend.sh` execs uvicorn with zero output redirection (confirmed by reading the script) and zero `ulimit`/`MALLOC_ARENA_MAX` enforcement of the config-declared `memory_cap_mb`/`malloc_arena_max` (confirmed via `/proc/<pid>/environ` on the live process) | FAIL | `reports/qa/goal-ops-hardening-iter-0-evidence/J-04-badge-initializing.png`, `J-04-badge-unavailable-crash.png`, `J-04-midflight-job-interrupted.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | happy-path | P1 | A single unsnapshotted day (2026-05-15) backfills, its aggregates (coverage/market-phase/membership) serve from storage on every subsequent read incl. across a restart, `/api/health` stays responsive during a heavy ingest job | Step 1 could not even be exercised as specified: the identical cadence-gate bug from J-01 gives the exact goal.md-suggested date (2026-05-15) `dates_total=0` too — no new snapshot was created to test storage-serving on. Independently confirmed FAIL for step 2: even a historically-productive backfill's persisted run message carries no record of which aggregates its finalize hooks refreshed (there are no such hooks — confirmed by source read of `_do_backfill`). Step 3 FAIL, live-measured: a cold restart + `GET /api/data` still took **10.055s** with RSS climbing steadily 646MB→1.75GB — the exact whole-table bar-prefill signature, not a persisted-payload read. Step 4 PASSED: `/api/health` answered all 32/32 polls (200) throughout a genuine ~10.8s heavy fetch-ingest job | FAIL | `reports/qa/goal-ops-hardening-iter-0-evidence/J-05-single-day-backfill-zero.png` |
| UT-J-06 | Pages load only what they need | happy-path | P1 | All 11 named pages load and are interactive within committed budgets; two new budget rows (boot time, current-basis cold `/api/data`) plus a code-audit statement are added to `reports/perf-budgets.md` | 8/11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/scanner-runs`, `/watchlist`, `/research/factor-lab`) rendered correctly and quickly with no observed budget concern. 3/11 (`/data`, `/evidence`, `/backtest`) were measured at 10-18s at the API level in this session — 5-12x the committed ≤1.5s/≤3s budgets — directly reproducing J-05's compute-on-request-path/cache-fragility finding (a fresh backfill/fetch invalidates the coverage/evidence cache, forcing the next hit to recompute from scratch; a repeat hit with no intervening ingest was fast again, 0.06-0.09s, confirming the cache itself works but is not ingest-maintained). No blank/frozen frame was observed (pages showed nav+shell while loading), but no explicit "loading…" progress indicator was seen either. The two new required budget rows and the code-audit statement are not yet in `reports/perf-budgets.md` | FAIL | `reports/qa/goal-ops-hardening-iter-0-evidence/J-06-backtest-still-loading.png` |

---

## Passed Tests

None scored a clean PASS in the strict PASS/FAIL/SKIP column this baseline (see UT-J-04 for a journey where 5 of 6 numbered steps passed live but the journey as a whole is scored FAIL because one required step is a confirmed, unambiguous miss).

No golden replay scripts were written this iteration (the golden-script instructions ask for one per journey **verified PASS**; none qualified).

---

## Failed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-0-evidence/J-01-may-backfill-zero-dates.png` (live "0 snapshots over 0 dates" result for the exact May request), `J-01-J-05-data-page-fullpage.png` (reloaded `/data` showing the persisted Run history table with 4 of my test runs, all `ok` status, no dates_total/reason columns), `J-01-data-initial.png` (pre-test state)

**Steps taken (live, Chrome MCP unless noted):**
1. Navigated to `/data`, set the backfill form to start `2026-05-02` / end `2026-05-29`, clicked Start.
2. Observed the "Job progress" panel: `backfill job · 2026-05-02 → 2026-05-29` → `ok` → **"backfill: 0 snapshots over 0 dates, 0 forward returns"**, elapsed 112ms, `0/0 dates`. Confirmed independently via a direct `POST /api/data/jobs` call (job `b70c6d87…`): `GET` on the job afterward returned `"dates_total": 0, "dates_done": 0, "snapshots_created": 0`, `"date_failures": []` (no reason field of any kind).
3. Navigated to `/scanner-runs`: only `2026-05-01` appears in the May 2026 rows (pre-existing from the seed) — none of `2026-05-04`, `2026-05-15`, `2026-05-29` exist.
4. Submitted the weekend-only span `2026-05-02 → 2026-05-03`: result "0 snapshots over 0 dates" — numerically correct by coincidence (0 trading days in a 2-day weekend), but rendered with the exact same generic text as every other zero-work outcome — no "2 non-trading days" reason breakdown.
5. Re-submitted the identical `2026-05-02 → 2026-05-29` range: again "0 snapshots over 0 dates" — indistinguishable from the very first attempt (there is no "already-snapshotted" vs "cadence-gate-filtered" distinction anywhere in the payload or UI).
6. Reloaded `/data` (full page navigation, not client-side routing): the "Job progress" panel — the panel with the rich stage-timing/badge UI — reset to **"No job has been started this session."**, the literal phrase the journey's acceptance explicitly forbids ("never 'no job started this session'"). The separate, plainer "Run history" table further down the page DOES survive reload and lists all 4 of my test runs plus prior history — but with columns STARTED/KIND/RANGE/STATUS/SYMBOLS OK-FAILED/SNAPSHOTS/SUMMARY only; no `dates_total` column, no exclusion-reason column, and every one of my 4 zero-work rows carries the same `ok` STATUS as the genuinely-productive historical rows (e.g. the `2026-01-01→2026-07-17` row with `25` snapshots) — visually indistinguishable badge/status.
7. Direct DB query (`data_provider_runs`) confirms the schema itself has no `dates_total`/exclusion-reason columns — only `id, provider, started_at, finished_at, symbols_ok, symbols_failed, status, message, dismissed, job_id`, with `message` a free-text JSON blob.

**Expected:** `dates_total = 19` for the May request; snapshots created for eligible in-range dates; explicit per-date exclusion reasons for every non-created date; persistence across reload including the live-progress panel; zero-work visually distinct from success.

**Actual:** `dates_total = 0` for every May request tried (the explicit-range-overrides-cadence rule does not exist in code — `_do_backfill` unconditionally applies `_cadence_allowed_dates`, and every May 2026 date is before `snapshot_cadence.daily_start: 2026-06-01`); no new snapshots; no structured reasons anywhere; the rich live-progress panel does not survive reload (regresses to the forbidden placeholder text); the plain Run history table does persist but cannot distinguish zero-work from success by status alone.

**Root cause (source-confirmed, not a UI-only gap):** `data_manager.py`'s `_do_backfill` target computation filters candidate dates through `_cadence_allowed_dates` with no explicit-request override, exactly as goal.md's own "Additional binding notes" anticipates needing to change ("requested range always wins" — not yet implemented).

---

### UT-J-03 — No per-run range cap

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-0-evidence/J-03-submit-attempt.png`

**Steps taken:**
1. Navigated to `/data`, set the backfill form to start `2025-06-01` / end `2026-07-17` (a 412-calendar-day span, >370).
2. Clicked Start.
3. The "Job progress" panel stayed on **"No job has been started this session."** — the submission never became a job. A distinct inline error line appeared directly under the form: **"date range too large: 412 days exceeds the configured maximum 370"** — captured verbatim via DOM text extraction and visible in the full-page screenshot.

**Expected:** The request is accepted — no "date range too large" rejection — and a live chunked-progress job begins.

**Actual:** The exact forbidden rejection message appears verbatim; no job is created. Source-confirmed: `config.yaml:57` still declares `max_range_days: 370`, and `data_manager.py`'s `validate_job_request` (~line 1834) still raises `ValueError(f"date range too large: {span_days} days exceeds the configured maximum {max_range_days}")` on any span over that cap. The three tests goal.md names as pinning the cap (`test_data_manager.py`, `test_api_data.py`, `test_config.py`) are unchanged.

---

### UT-J-04 — Non-blocking boot with visible status

**Verdict:** FAIL (5 of 6 numbered steps passed live; scored FAIL because step 5 is a confirmed, unambiguous miss and the journey's own Correctness acceptance ties to it)

**Evidence:** `reports/qa/goal-ops-hardening-iter-0-evidence/J-04-badge-initializing.png`, `J-04-badge-unavailable-crash.png`, `J-04-midflight-job-interrupted.png`

**Steps taken (two independent full stop/start cycles, plus one simulated crash):**
1. Stopped the running backend (`SIGTERM`, confirmed port released), restarted via `scripts/start-backend.sh` (CHAIN_BACKEND_PORT=8255, matching CORS), timing from process launch with a 150ms-interval poller: **first HTTP 200 at t=0.909s** — well inside the 5s budget. Repeated on a second restart: **first 200 at t≈1.05-1.24s** (three restarts total this session, all ≤1.3s).
2. On the first restart, polled `/api/health` continuously: readiness stayed `"initializing"` with `warmup: {done:89, total:89, status:"running", message:"history 89/89"}` from t=0.909s through t=13.245s, flipping to `"ready"` at t=13.981s — a genuine ~13s pre-ready window. During that exact window, navigated the already-open frontend to `/` and read the readiness badge's DOM directly: `data-state="initializing"`, text **"Initializing… history 89/89"** — matching the health payload's phase/progress exactly, never a bare "unavailable." Screenshot: `J-04-badge-initializing.png`.
3. Killed the backend with `kill -9` (simulated crash). Immediately re-read the badge: `data-state="unavailable"`, text **"Backend unavailable"** (red) — and the layout's separate preflight banner independently flipped to **"NO-GO — do not rely on today's board. Backend is unavailable — the preflight check could not run."** Both presentations are visibly distinct from the amber "Initializing…" state. Screenshot: `J-04-badge-unavailable-crash.png`.
4. Restarted the backend a third time. Immediately before that restart, fired `POST /api/data/jobs` (`fetch`, 2020-01-01→2021-01-01, source `yahoo`) and captured `status: "running"`, then `kill -9`'d the backend within the same shell command (no intervening sleep) to guarantee the job was genuinely mid-flight. After the restart, the DB `data_provider_runs` row for that `job_id` reads **`status = "interrupted"`** (with `finished_at` populated by the boot-time sweep), and the `/data` page's Run history table shows the same row with **STATUS = interrupted** — never a stuck "running" row with no living process. Screenshot: `J-04-midflight-job-interrupted.png`.
5. **FAIL, confirmed two ways:** (a) source read of `scripts/start-backend.sh` — the full file execs uvicorn directly (`exec ... uvicorn main:app --host 0.0.0.0 --port "$PORT" --app-dir ...`) with zero output redirection, zero `ulimit`, zero `MALLOC_ARENA_MAX` export; (b) operationally, `cat /proc/<pid>/environ` on the live restarted process shows no `MALLOC_ARENA_MAX`/`memory_cap`-related variable at all. The only reason ANY stdout log existed to inspect during this test session is that *I* (the QA agent) manually redirected uvicorn's stdout/stderr to a scratch file for my own timing harness — a user running the documented script directly would get no persistent logfile at all, and `config.yaml`'s declared `server.memory_cap_mb: 6144` / `malloc_arena_max: 2` are enforced nowhere.

**Expected:** All 6 numbered steps hold, including a persistent backend logfile (with boot events, ending abruptly with no clean-shutdown line after a crash) and applied memory-cap enforcement.

**Actual:** Steps 1-4 (and 6, counting the interrupted-job check as step 6) all reproduced live exactly as required — this half of the journey already works (inherited from mcp-loop iter-28/iter-33, per the dev handoff, now empirically confirmed). Step 5 is unimplemented: no product-created persistent logfile, no memory-cap/arena enforcement.

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly

**Verdict:** FAIL (1 of 4 steps passed)

**Evidence:** `reports/qa/goal-ops-hardening-iter-0-evidence/J-05-single-day-backfill-zero.png`

**Steps taken:**
1. Confirmed via DB query that `2026-05-15` has bars (589 symbols) but no `scanner_runs` row — a genuine backfill gap, and the exact date goal.md's own step 1 suggests. Submitted a backfill for start=end=`2026-05-15` via the `/data` form. Result: **the same cadence-gate bug as J-01** — `"backfill: 0 snapshots over 0 dates, 0 forward returns"`, 111ms elapsed. 2026-05-15 is before `daily_start: 2026-06-01`, so it is filtered out exactly like the J-01 May range was. **No new snapshot was created — step 1 cannot be exercised as specified**, because it shares J-01's root cause rather than being a separate, isolated bug.
2. Read `_do_backfill`'s finalize/`_persist` closure (source) and a historically-productive run's persisted message (the `2026-01-01→2026-07-17` run, `25 snapshots over 25 dates`): the message string is `"backfill: N snapshots over M dates, K forward returns"` with **no mention of coverage/market-phase/membership-timeline/research-cache refresh** — because no such finalize hook exists in the code (confirmed: only `scanner.persist_run_payload` + `forward_testing.backfill_run_forward_returns` run per date).
3. **Live-measured**, independent of steps 1-2: stopped the backend, restarted cold, then concurrently (a) polled `/api/health` every 200ms and (b) issued one `GET /api/data` and timed it end-to-end while sampling the process's `VmRSS`. Result: **`/api/data` took 10.055s**, with RSS climbing steadily and monotonically from 646MB → 1,750MB over the request's duration, then falling back to ~832MB afterward — the exact whole-table bar-prefill signature `reports/perf-budgets.md` and goal.md's own "Ground truth" section document as the offender, not a fast persisted-payload read.
4. Concurrently with a genuine ~10.8s heavy `fetch` ingest job (591-symbol fetch over a full year), polled `/api/health` every 200ms: **32/32 polls returned 200** — the backend stayed responsive throughout. This one sub-check **PASSED**.

**Expected:** A single-day backfill creates a new stored snapshot whose aggregates (coverage, market phase, membership) are then served from storage everywhere, including across a cold restart, with `/api/health` staying responsive during heavy ingest.

**Actual:** The suggested single-day backfill cannot even ingest (shared J-01 cadence bug); no finalize hook refreshes any named aggregate; a cold `/api/data` still pays the full ~10s/1.75GB whole-table prefill instead of serving a persisted payload. Only the health-responsiveness-during-ingest sub-claim held.

---

### UT-J-06 — Pages load only what they need

**Verdict:** FAIL (8 of 11 pages healthy; 3 measured far outside budget; required new artifacts absent)

**Evidence:** `reports/qa/goal-ops-hardening-iter-0-evidence/J-06-backtest-still-loading.png`

**Steps taken:**
1. With the backend warm (post-restart, `readiness: ready`), navigated via Chrome MCP to all 11 named surfaces: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/factor-lab`. 8 of them (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/scanner-runs`, `/watchlist`, `/research/factor-lab`) rendered their real heading + populated content promptly with no observed delay or console-visible crash.
2. `/data`, `/evidence`, `/backtest` were measured at the API level (warm `curl -w '%{time_total}'`, run in the same session immediately after several backfill/fetch jobs from the J-01/J-03/J-04/J-05 tests above): `/api/data` **13.335s**, `/api/backtest` **14.518s**, `/api/evidence` **17.738s** — all 5-12x over the committed `≤1.5s` (endpoints) / `≤3s` (pages) budgets in `reports/perf-budgets.md`. Repeating the SAME `/api/data` call twice more with no intervening ingest returned in **0.060s** and **0.093s** — proving the in-process cache itself works, but is invalidated by any backfill/fetch and is not proactively refreshed at ingest time, so the very next read anywhere pays a full recompute. This is J-05's already-documented root cause surfacing as a page-load budget violation, not an independent new bug.
3. Corresponding page loads for `/evidence` and `/backtest` showed a partial shell (nav + banner rendered, heading visible, main content area a low-interactive-element skeleton) for several seconds before real content appeared — no blank/frozen application-error page was observed, but no explicit "Loading…" progress indicator was seen either.
4. Confirmed (re-reading `reports/perf-budgets.md`, 621 lines) that the existing endpoint/page budget rows from mcp-loop (iter-19 through iter-42) are still present and were last shown holding on 2026-07-16 — but no row exists yet for "process start → first `/api/health` 200 ≤5s" (this iteration's own J-04 measurement above, 0.909-1.24s, is NOT yet recorded there) nor for a cold `/api/data` figure on the current post-iter-41 data basis, and no committed code-level audit statement ("no on-load endpoint performs an unbounded `daily_prices` scan") exists as its own artifact — matching the dev handoff's own gap-finding.

**Expected:** All 11 pages interactive within committed budgets; the two new required budget rows plus a code-audit statement recorded in `reports/perf-budgets.md`.

**Actual:** 8/11 pages are fast and healthy; 3/11 (exactly the three that read the coverage/evidence/backtest aggregates) blow through budget by 5-12x under the realistic condition of "a backfill/fetch just ran" — which J-01/J-03's own journeys require as normal operation; the two new budget rows and the audit statement are not yet committed.

---

## Skipped Tests

None. Chrome MCP and both services (backend :8255, frontend :3255, prod mode) were available throughout.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (prod mode, `scripts/start-backend.sh`; restarted 3x live during this QA pass for J-04/J-05 timing/crash tests, always confirmed healthy again before moving on)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-19
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-0-evidence/`
- **DB touched:** the live dev SQLite DB (`apps/backend/data/trendora.db`) gained several new `data_provider_runs` rows from the backfill/fetch jobs this QA pass submitted (all offline, seed/fixture-backed, no live network calls per AG-9) — no schema change, no seed-data deletion, no source/config file touched. `git status`/`git diff` show zero changes under `apps/` or `config.yaml` from this step.
- **Golden replay scripts:** none written this iteration — no journey reached a clean PASS (see "Passed Tests" above).

---

## Cross-reference with the developer step's preliminary analysis

Every FAIL above independently reproduces, with live evidence, what `docs/handoffs/goal-ops-hardening-iter-0-dev.md`'s code-level (static) pass had already flagged as "preliminary FAIL/PARTIAL." Nothing in this live pass contradicts that analysis; this report adds the empirical confirmation the dev handoff explicitly deferred to browser-QA (exact `dates_total` values observed, exact rejection message text, measured boot/crash timings and badge states, measured cold `/api/data` wall-time and RSS growth).
