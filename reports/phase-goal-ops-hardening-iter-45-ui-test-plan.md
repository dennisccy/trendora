# Phase goal-ops-hardening-iter-45 — UI Test Plan

**Phase:** goal-ops-hardening-iter-45
**Date:** 2026-08-04
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration. The phase spec's own metadata states "New user-facing
capability: None", "New information displayed: None", "New user actions: None", and "UI surface
changes: None", and `git status`/`git diff --stat HEAD` confirm **zero files under `apps/frontend/`**
changed this iteration. Every changed file this iteration is backend engine code
(`apps/backend/app/engine/data_manager.py`), a backend test file (`apps/backend/tests/test_data_manager.py`),
or the golden-script anchor refresh (`runs/goal-session-ops-hardening/journey-scripts/J-07.json`). Per
the "Backend-only phase handling" rule, this test plan emits exactly one `UT-<journey-id>` regression
test case for **every journey named on EITHER** the phase spec's `Required-still-passing journeys:` line
**OR** its `Target journeys:` line.

This iteration's metadata names:
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
- **Target journeys:** J-05, J-07

Union of both lines = 8 distinct journeys, no duplicates — the same set as iter-44's plan (a prior
ESCALATE verdict forces full-depth + full regression again this iteration).

**Grounding:** each test case below combines three sources — (1) the checked-in automated replay
script at `runs/goal-session-ops-hardening/journey-scripts/J-<NN>.json` (canonical URLs/testids/button
roles/expected text — `git diff` confirms only `J-07.json` changed this iteration, its two anchors from
`n=8878`→`n=8991` and `3508`→`2533`; all other scripts are byte-identical to iter-44's), (2) the fuller
narrative "Steps"/"Acceptance" text for that journey in `docs/goal.md`'s "Must-have user journeys"
section, and (3) a LIVE check of the running backend/frontend at http://localhost:8255 /
http://localhost:3255 performed while writing this plan (both were already up and warm — see the KNOWN
OPEN RISK section for exactly what that live check found, including one live-confirmed discrepancy in
the freshly-updated `J-07.json` anchor itself). Where sources diverge in a figure, the script's asserted
text is authoritative for the automated replay, but the live-verified value is what a human operator will
actually see on screen right now — both are called out explicitly below wherever they differ.

**Not covered by this document (no browser-observable surface exists for these):**
- **TC-1 / TC-2 / TC-3** — the append-forward fast path's internal correctness (call-count proof that
  `resolve_with_reasons` is invoked only for new dates; byte-for-byte reuse of cached points; byte-identity
  against the pre-fix full-recompute oracle). These are properties of a server-side cache/compute path with
  no rendered difference in any response shape — verified by
  `apps/backend/tests/test_data_manager.py`'s four new tests
  (`test_append_forward_ingest_does_not_reinvoke_resolver_for_cached_dates`,
  `test_append_forward_reuses_cached_points_byte_for_byte`,
  `test_append_forward_fast_path_byte_identical_to_full_recompute`,
  `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse`) and the reviewer's independent
  re-run of the same suite plus the existing 10-test `test_data_manager_membership_cache.py` regression
  file (all pass per `reports/reviews/goal-ops-hardening-iter-45-review.md`).
- **TC-8** — the closed third `MemoryError` escape inside `_refresh_ingest_aggregates`'s own
  `logger.exception()` call. A logging-path bug with no user-visible symptom other than "the job silently
  died instead of finishing with an honest error" — not something a browser session can trigger on demand;
  verified by 5 consecutive clean runs of `apps/backend/tests/test_ingest_finalize_memory_pressure.py`
  (per the dev handoff: runs of 156.12s/154.49s/151.34s/148.89s/147.94s, all 2 passed, zero escapes).
- **TC-10** — the corrected stale comment in `_fail_unlaunched_job` (`data_manager.py`). A code comment,
  never rendered anywhere.

**KNOWN OPEN RISK — read before executing UT-J-05 and UT-J-07. This is the single most important thing
in this document.**

This iteration's own dev handoff, the reviewer's independent review (`PASS_WITH_NOTES`,
`reports/reviews/goal-ops-hardening-iter-45-review.md`), and a fresh live check performed while writing
this plan **all agree**: the append-forward fast path only accelerates a backfill whose new date(s) are
`>=` every date already cached in the membership-timeline payload. I checked the live committed DB
directly (read-only queries, no compute triggered):

- `GET http://localhost:8255/api/data` right now reports `coverage.snapshot_count: 2863`,
  `coverage.gap_count: 2532`, `coverage.gap_first: "2005-05-16"`, `coverage.gap_last: "2019-02-25"`.
- A direct query of `scanner_runs` confirms `2019-02-26` (id 2863), `2019-02-27` (id 2862), and
  `2019-02-28` (id 2861) are ALL already snapshotted — `2019-02-26` was snapshotted by THIS iteration's
  own dev-verification pass (disclosed in the dev handoff's "Known Issues" / "Side effect" notes).
- Every trading day between `2019-02-27` and the data horizon (`2026-07-31`) already has a snapshot.
  **Every remaining gap in this database is chronologically EARLIER than the current cached boundary** —
  i.e. every backfill target available to test today is a historical gap-fill, the ONE case this
  iteration's fast path explicitly does not accelerate (by design — `assumptions.md` iter-45's second
  entry, and the phase spec's own "Out of Scope" section).
- The nearest such gap to the boundary is **`2019-02-25`** (`coverage.gap_last` above) — confirmed absent
  from `scanner_runs` by direct query at the time this plan was written.
- The default date baked into `journey-scripts/J-05.json` (`2005-04-12`, expecting run id `1882`) is
  **already snapshotted** (confirmed live: `scanner_runs` has a row with `asof_date='2005-04-12'` and
  `id=1882`) — the automated replay's own default target is stale and must be substituted before running.

This iteration's dev handoff records a real, timed drill of the adjacent gap-fill case (`2019-02-26`,
before it was filled): the backfill job was **still `"status": "running"` at t=1106s** when observation
stopped — past both TC-4's 300s budget and iter-44's prior ~1,001s reference point for the same class of
stall. This is the code's EXISTING, unchanged full-recompute fallback running exactly as before this
iteration — not a regression, and explicitly out of this iteration's scope. **Whoever executes UT-J-05
below should expect the same outcome from `2019-02-25` and must record the ACTUAL elapsed time and ACTUAL
terminal state observed, not an assumed pass or fail** — the reviewer's own review report flags this exact
risk and defers the grading judgment call to QA/the evaluator, not to this document.

**A second, independently-confirmed discrepancy affecting UT-J-07 specifically:** `journey-scripts/J-07.json`
was updated THIS iteration to assert `"2533"` on `/data` (replacing the stale `3508`). That refresh was
correct at the moment it was captured. But the SAME dev pass's own later live-verification backfill of
`2019-02-26` (disclosed above) filled one MORE historical gap after the anchor was captured — so the
LIVE value as of this plan being written is **`2532`**, not `2533` (`GET /api/data` → `coverage.gap_count:
2532`, confirmed above; the frontend renders this raw, unformatted, at `apps/frontend/app/data/page.tsx`
via `value={c.gap_count}`). **The automated replay of `J-07.json` step 3, as currently checked in, will
fail its literal `"2533"` text match against a fresh page load right now.** This number decrements by one
every time any historical gap gets backfilled by ANY pipeline stage's own live drilling (dev, review, QA,
or this analysis pass all query/exercise the same shared, uncommitted `apps/backend/data/trendora.db`) —
so the exact figure may have moved again by the time this plan is executed. The human test case below is
written against the number CONFIRMED LIVE at the time of writing (2532), with an explicit instruction to
re-read the actual on-screen figure rather than assume either 2533 or 2532 is still current.

**Positive, disclosed finding carried into UT-J-07:** the dev's ~1,106s single-gap-fill drill found
`GET /api/health` returned HTTP 200 on every poll across the whole observation window — no freeze, no
connection-refused, nothing resembling iter-44's 20+-minute outage. This is favorable evidence for
J-07's "health stays responsive" acceptance class, independent of whether the triggering backfill itself
completes quickly.

---

## Test Cases

---

### UT-J-01 — Backfill honors the requested range and explains zero-work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/748`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- No login required
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (unchanged this
  iteration)
- Note: this exact journey was already re-run live earlier in this iteration's own pipeline (backend
  `data_provider_runs` rows 273/275 record clean `"ok"` completions for both steps below) — it is
  expected to be a fast, unsurprising PASS

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2026-05-02` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-05-03` into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button
5. Watch the "Job progress" panel (`data-testid="job-status"`) until it leaves the "running" state
6. Reload `http://localhost:3255/data`
7. Type `2026-05-02` into "Start date" and `2026-05-29` into "End date"
8. Click "Start" again
9. Watch "Job progress" (`data-testid="job-status"`) until it leaves "running"
10. Reload `http://localhost:3255/data`
11. Navigate to `http://localhost:3255/scanner-runs/748`

**Expected Result:**
- After step 5: the run's summary text includes "2 non-trading" (the weekend-only span — 0 trading-day
  targets, 2 non-trading days)
- After step 9: the run's summary text includes "19 already snapshotted" (re-running the full May range
  is zero-work in this DB's current state)
- Both zero-work outcomes render as a visually distinct explanatory badge/state — NOT the same plain
  green success badge a productive first-time run would show
- After step 10: the "Run history" table still lists BOTH runs from steps 4 and 8 — reloading does not
  clear job history
- Step 11: `/scanner-runs/748` renders the text "as of 2026-05-29" with a populated leaderboard table
  (not the "No stored stock rows" empty state)

---

### UT-J-03 — No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- Navigate to a fresh load of `/data` (no job currently running)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-03.json` (unchanged this
  iteration)
- Note: this exact 412-day range was already re-run live earlier in this iteration's own pipeline
  (`data_provider_runs` row 274 records `dates_done: 283/283`, `calendar_days: 412`, a clean `"ok"`
  completion in well under a second, since all 283 dates were already snapshotted)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-07-17` into the "End date" field (`data-testid="job-end-date"`) — a 412-calendar-day span
4. Click the "Start" button
5. Watch the "Job progress" panel (`data-testid="job-status"`) and the live activity line
   (`data-testid="job-live-activity"`, `data-testid="job-heartbeat"`) for at least a few seconds
6. Once the job reaches a terminal status, reload `http://localhost:3255/data`

**Expected Result:**
- No text such as "date range too large" (or any range-cap rejection message) appears near the form at
  any point
- Step 5: the job transitions to (and, briefly, stays in) a running state — confirms the request was
  accepted, not rejected outright. Given every date in this range is already snapshotted, expect this to
  resolve very quickly (well under the golden script's own budget), not a multi-minute run
- Step 6: the run's summary text in "Run history" includes the literal text "412 calendar days"

---

### UT-J-04 — Non-blocking boot with visible status (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/`, `/data`, preflight banner

**Preconditions:**
- Frontend already open at `http://localhost:3255/`
- Operator has terminal access to stop/restart the backend via `scripts/start-backend.sh` and to send a
  hard `kill`
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-04.json` (unchanged this
  iteration)

**Steps:**
1. With `http://localhost:3255/` open, stop the backend, then restart it via `scripts/start-backend.sh`
2. Immediately watch the top-bar readiness badge (`data-testid="readiness-badge"`) and, in a terminal,
   poll `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8255/api/health`
3. Once the badge reads "Ready", reload `http://localhost:3255/` and confirm the page text includes
   "provider: seed"
4. Navigate to `http://localhost:3255/data` and confirm the page shows a "Run history" section
5. Kill the backend process directly (`kill <pid>`, NOT a clean `scripts/start-backend.sh` stop —
   simulates a crash)
6. Watch the badge/banner again
7. Tail `logs/backend.log` around the kill
8. Restart the backend again via `scripts/start-backend.sh`; navigate to `/data`

**Expected Result:**
- Step 2: the badge passes through `data-state="loading"` or `data-state="initializing"` before settling
  on `data-state="ready"` with visible text "Ready" — never blank; the first `/api/health` HTTP 200
  arrives within 5 seconds of process start. Note: this iteration's own drilling put ~2,863 snapshot dates
  and a `591`-symbol pool through repeated warm-ups without incident, so boot should behave identically to
  iter-44
- Step 3: the dashboard renders the text "provider: seed"
- Step 4: `/data` renders a populated "Run history" section — not blank, not stuck loading. Expect the
  Run History table to contain entries left over from this iteration's own dev/review drilling (multiple
  backfill rows for `2019-02-26`, `2026-07-31`, `2026-05-02`, and the wide `2025-06-01`→`2026-07-17`
  range) — this is expected, disclosed accumulation, not a fresh bug
- Step 6: the badge shows `data-state="unavailable"` with text "Backend unavailable", and/or the preflight
  banner renders the unreachable reason
- Step 7: the tailed log shows boot entries but ends abruptly with no clean-shutdown entry right before
  the gap
- Step 8: any job that was mid-flight at the kill now shows an explicit interrupted/error state on
  `/data` — never a still-"running" row with no living process

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/<new run id>`, global readiness badge

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- Operator has terminal/log access to tail `logs/backend.log` and can restart the backend via
  `scripts/start-backend.sh`
- No login required
- **Before starting, confirm the chosen date is genuinely absent from `/scanner-runs`** by navigating to
  `http://localhost:3255/scanner-runs` and searching for the date, or via
  `GET http://localhost:8255/api/data` and reading `coverage.gap_last` (the nearest remaining gap to the
  cached boundary). Do NOT use the golden script's baked-in default (`2005-04-12`) — it is **already
  snapshotted** (confirmed live: `scanner_runs` row id `1882`, `asof_date='2005-04-12'`). At the time this
  plan was written, the live-verified nearest gap was **`2019-02-25`** (`coverage.gap_last`) — use that
  unless a re-check at execution time shows it has since been filled by another pipeline stage's own
  drilling, in which case pick whatever date `coverage.gap_last` reports then.
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  (`default_timeout_ms: 60000` — this budget will very likely NOT be met this iteration; see below)

**See the "KNOWN OPEN RISK" section at the top of this document — it applies directly to steps 4, 8-9
below, and the expected result is very likely a documented, disclosed miss rather than a clean pass.**

**Steps:**
1. Navigate to `http://localhost:3255/data` (confirm heading "Data Manager")
2. Type `2019-02-25` (or your freshly re-confirmed unsnapshotted date) into the "Start date" field
   (`data-testid="job-start-date"`)
3. Type the SAME date into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button; note the wall-clock start time
5. While the job runs, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
6. In the "Run history" table, find the new row and note its run id; navigate to
   `http://localhost:3255/scanner-runs/<that id>`
7. Return to `http://localhost:3255/data`
8. Find the "Run history" row for the run started in step 4
9. Read its "Refreshed:" text (`data-testid="aggregates-refreshed"`). Per this iteration's own disclosed
   finding, expect this to still read "running" well past the 300-second TC-4 budget — this iteration's
   own dev drill of the adjacent date left the SAME class of job still `"running"` at t=1106s. Check every
   few minutes for up to 20 minutes and record the ACTUAL wall-clock time when (and if) it reaches a
   terminal state
10. Restart the backend via `scripts/start-backend.sh`; immediately load `http://localhost:3255/data` cold
    (the first request after restart)
11. Tail `logs/backend.log` around the restart and the cold `/data` request from step 10

**Expected Result:**
- Step 5: the badge stays at `data-state="ready"` throughout — never switches to `data-state="unavailable"`
  while the backfill and its finalize warm run (this is the ONE part of J-05/J-07's acceptance this
  iteration's own drilling found solid evidence for)
- Step 6: the scanner-run page shows the text "as of 2019-02-25" (or your substitute date) with a
  populated leaderboard — the create-once scan stage itself (distinct from the finalize tail below) is
  UNCHANGED by this iteration and should resolve quickly
- Step 9: **record the literal observed text and elapsed time — do not assume pass or fail.** Given this
  iteration's disclosed scope (the append-forward fast path does not accelerate historical gap-fills, and
  every remaining gap in this DB IS a historical gap-fill), the most likely honest outcome is the row
  still reading "running" at the 20-minute mark, matching the dev's own 1106s+ live observation of the
  adjacent date. If it DOES complete, "Refreshed:" should list "latest snapshot", "coverage", and "forward
  aggregates". Either outcome is consistent with this iteration's own disclosed, unresolved finding for
  the gap-fill case — report the literal state, and flag it to QA/the evaluator as the reviewer's own
  report already anticipates (a scope judgment call, not a fresh defect)
- Step 10: `/data`'s "Dataset coverage" panel (`data-testid="universe-count"`,
  `data-testid="candidate-universe-count"`) renders populated numeric values promptly, not a blank/error
  panel and not an indefinite spinner
- Step 11: the tailed log around the restart and cold `/data` request contains no line indicating a
  full-table / 3.3M-row bar prefill for that request

---

### UT-J-06 — Pages load only what they need (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (not `dev.sh`), warm (already served at
  least one request)
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh`)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (unchanged this
  iteration)

**Steps:**
1. Navigate to `http://localhost:3255/` and note time-to-interactive — confirm text "Dashboard"
2. Navigate to `http://localhost:3255/stocks` — confirm text "Stocks"
3. Navigate to `http://localhost:3255/stocks/AAPL` — confirm text "AAPL"
4. Navigate to `http://localhost:3255/sectors` — confirm text "Sectors"
5. Navigate to `http://localhost:3255/themes` — confirm text "Themes"
6. Navigate to `http://localhost:3255/data` — confirm text "Data Manager"
7. Navigate to `http://localhost:3255/evidence` — confirm text "Evidence"
8. Navigate to `http://localhost:3255/scanner-runs` — confirm text "Scanner Runs"
9. Navigate to `http://localhost:3255/backtest` — confirm text "Backtest"
10. Navigate to `http://localhost:3255/watchlist` — confirm text "Watchlist"
11. Navigate to `http://localhost:3255/research/regime-lab` — confirm text "Research — Regime Lab"

For each page, record time-to-interactive and note any on-load API call that errors or takes noticeably
long.

**Expected Result:**
- Every page above renders its listed anchor text within its committed budget in the most recently
  recorded `reports/perf-budgets.md` section — no page hangs indefinitely or shows a blank/error frame.
  This iteration's diff touches no page-load path (only the ingest finalize hook), so no change from the
  prior iteration's measured load times is expected; a fresh, dated `reports/perf-budgets.md` "Iteration
  45" section recording TC-6's numbers is still owed as part of executing this test case (the dev handoff
  does not add one — the developer's own time-budget drills are logged in the handoff itself, not this
  file)
- Flag explicitly (do not round to "close enough") any page whose load time regresses versus the last
  recorded budget — `/stocks`, `/sectors`, and `/themes` remain the pages most exposed to the still-open
  `_SymbolColumns`/`bars_asof` per-call slicing cost named in iter-44's live diagnostic; no code fix
  shipped for it this iteration, so no change in these pages' load times is expected

---

### UT-J-07 — Heavy aggregates never take the service down (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Scope note:** this covers J-07 acceptance steps 1-2 only (the browser/operator-observable subset).
Steps 3-4 (VmPeak measurement, a synthetic memory-pressure abort via a test hook) are not observable
through the UI — see `apps/backend/tests/test_ingest_finalize_memory_pressure.py` /
`test_ingest_finalize_fault_injection.py` and the dev handoff's TC-8 section (5/5 clean runs).

**See the "KNOWN OPEN RISK" section at the top of this document — it applies directly to step 3 below
(the `journey-scripts/J-07.json` anchor is already one gap-fill stale) and to step 8.**

**Preconditions:**
- Frontend running at http://localhost:3255, backend running in prod mode via
  `scripts/start-backend.sh` (not `dev.sh`), reachable at http://localhost:8255/api/health
- Operator has a terminal to time-poll health, e.g.
  `curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://localhost:8255/api/health`
- A wide, not-yet-fully-snapshotted date range is available to trigger a heavy multi-date backfill and
  its forward-aggregate warm. Note: as of this plan's writing, `2025-06-01`→`2026-07-17` (used by UT-J-03)
  is now FULLY snapshotted (`already_snapshotted: 283/283` per `data_provider_runs` row 274) and will no
  longer trigger heavy work — use a range that includes at least one confirmed gap, e.g.
  `2019-01-01`→`2019-02-25` (spans the live-confirmed unfilled region below the `2019-02-26` boundary), or
  re-check `GET /api/data`'s `coverage.gaps_preview` for a current wide gap
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (its two dataset
  anchors were refreshed THIS iteration: `n=8878`→`n=8991` on `/backtest`, `3508`→`2533` on `/data`)

**Steps:**
1. Navigate to `http://localhost:3255/` — confirm text "Ready" (fast sanity anchor)
2. Navigate to `http://localhost:3255/backtest` — confirm text "n=8991" (this iteration's freshly-updated,
   live-verified anchor — confirmed present in the live `GET /api/backtest` response's Return Attribution
   Bucket A row at the time this plan was written)
3. Navigate to `http://localhost:3255/data` — look for the "Backfill gaps" stat
   (`data-testid` not required — it is the labeled number under "Backfill gaps"). **The script asserts
   `"2533"`, but the LIVE value confirmed while writing this plan is `"2532"`** (one fewer, because this
   iteration's own dev-verification drill filled the `2019-02-26` gap after the anchor was captured, and
   this count keeps decrementing as other pipeline stages run their own drills against the same shared
   DB). Read the actual number shown and record it — treat an exact match to `2533` OR a plausible nearby
   value (e.g. `2532`, or one fewer still if another drill ran between writing and executing this plan) as
   a PASS for "the panel renders a real number consistent with a very recently filled gap"; treat a wildly
   different number, a blank panel, or an error as a FAIL
4. On `/data`, type a wide unsnapshotted date range into "Start date" (`data-testid="job-start-date"`)
   and "End date" (`data-testid="job-end-date"`) — see the range note in Preconditions above — then click
   "Start". This triggers the full-horizon forward-aggregate warm via the ingest finalize path
5. While the job runs, in a terminal run the timed curl command above once every 5-10 seconds for at
   least 5 minutes (longer if practical); log EVERY response's HTTP code AND its `time_total`
6. At the same time, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
7. Still while the job runs, open `http://localhost:3255/backtest` in a second tab
8. After the "Run history" row's "Refreshed:" text (`data-testid="aggregates-refreshed"`) includes
   "forward aggregates", reload `http://localhost:3255/backtest`. Per the KNOWN OPEN RISK note, if the
   triggering range includes a historical gap-fill this may not happen within a short observation window —
   if the row still reads "running" after 20+ minutes, record that literally rather than waiting
   indefinitely

**Expected Result:**
- Steps 1-2: both golden anchors render (confirms the baseline surfaces are healthy before the heavy job
  starts)
- Step 3: a real numeric "Backfill gaps" value renders — see the note above on the exact figure
- Step 5: this iteration's own dev drill found EVERY polled `/api/health` response returned HTTP 200
  across a ~1,106s observation window (zero non-200, zero connection failures) while a gap-fill backfill
  ran — expect the same. Report the ACTUAL pass rate and any latency spikes observed rather than assuming
  a clean pass; any non-200 response or a response taking many seconds IS worth flagging as new
- Step 6: the badge stays at `data-state="ready"` throughout — never `data-state="unavailable"`
- Step 7: `/backtest` renders promptly — either normal evidence values, or the "Refreshing — showing the
  last complete evidence" banner (`data-testid="evidence-refreshing"`) — never a blank page or an
  indefinitely-frozen skeleton. **Note:** at the time this plan was written, `/backtest` was ALREADY
  serving `evidence_status="refreshing"` (from earlier drilling this session, before you even trigger step
  4) — if that is still true when you reach step 7, the banner being visible immediately is expected, not
  a new finding
- Step 8: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone — OR, per
  the KNOWN OPEN RISK note, the row may still read "running" well past 20 minutes if the triggering range
  included a gap-fill; report the literal state rather than waiting indefinitely or assuming failure

---

### UT-J-08 — Backtest serves stored evidence, never a cold recompute (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`, `/data`

**Preconditions:**
- A forward-aggregate warm has completed at least once already for the current dataset version (so a
  "last-good" version exists to fall back to) — already true right now: `GET /api/backtest` currently
  serves `evidence_status="refreshing"` with the last-good Bucket A `n=8991` figure, a live, ready-made
  example of exactly the behavior this test verifies
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-08.json` (unchanged this
  iteration)

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Forward-tested evidence"
2. Note the served as-of date and evidence figures shown on the page right now
3. Navigate to `http://localhost:3255/data`; start a small single-day backfill on a date not yet
   snapshotted (set both "Start date" and "End date", `data-testid="job-start-date"` / `job-end-date`, to
   the same date — reuse the date confirmed via `coverage.gap_last` for UT-J-05 above if it is still
   unfilled — then click "Start")
4. While that job's finalize warm is still running (Job progress panel reads "running"), navigate back to
   `http://localhost:3255/backtest`
5. Observe the evidence panel
6. After the "Run history" row for the job lists "forward aggregates" among its refreshed aggregates
   (`data-testid="aggregates-refreshed"`), reload `http://localhost:3255/backtest`. Per this iteration's
   disclosed finding (see KNOWN OPEN RISK), a gap-fill's finalize tail can take well over 15 minutes to
   reach this state — if it has not completed within a reasonable wait, it is acceptable to confirm steps
   4-5's behavior thoroughly and record step 6 as "not reached within the observation window"

**Expected Result:**
- Step 1: the text "Forward-tested evidence" is visible
- Steps 4-5: `/backtest` renders promptly — either normal served values from the PREVIOUS version, or the
  banner "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`) — never a
  blank page or an indefinite loading skeleton
- Step 6 (if reached): `/backtest` now shows the new version's values (a different served as-of / updated
  numbers from step 2) and the "Refreshing…" banner is gone

---

### UT-J-09 — Background-compute activity is disclosed on the badge and `/data` panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Preconditions:**
- Backend warm; at least one historical as-of exists whose forward-aggregate evidence is not yet complete
  for the current dataset version — currently true (`evidence_status="refreshing"` is already being
  served, per UT-J-08's precondition)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-09.json` (unchanged this
  iteration)

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Time-machine"
2. Click the "Previous available date" button (`aria-label="Previous available date"`) enough times to
   land on a historical as-of whose evidence is not yet computed for the current dataset version
3. Confirm the page shows text "(historical)"
4. Immediately look at the top-bar badge (`data-testid="readiness-badge"`)
5. Navigate to `http://localhost:3255/data` and find the "Background compute" panel
   (`data-testid="background-compute-panel"`)
6. Read the panel's disclosure text
7. Wait for the window to complete, then re-check the badge and the panel's "Last outcome" section

**Expected Result:**
- Step 3: the page shows "(historical)" next to the selected as-of — confirms the request returned
  immediately without blocking on the background dispatch
- Step 4: the badge still reads "Ready" AND shows an additional accent chip
  (`data-testid="background-compute-indicator"`) whenever a window is actually in flight — as of this
  plan's writing `GET /api/health`'s `background_compute.active` array is empty (idle), so if no window is
  currently in flight when you reach this step, trigger one first (e.g. via UT-J-05/UT-J-07's backfill) or
  note the idle state honestly rather than reporting a false PASS
- Step 6: when a window IS in flight, the panel lists it with elapsed time and horizons done/total, and
  somewhere on the page the text "process-lifetime only, never persisted" is visible
- Step 7: after completion, the chip disappears from the badge and the panel's "Last outcome" section
  shows the completed window's outcome with a real measured duration — never a silent failure or an
  unexplained forever-refreshing state. If the window does not complete within a practical wait (see the
  KNOWN OPEN RISK note), record that honestly

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | `/data`, `/scanner-runs/748` |
| UT-J-03 | No per-run range cap | regression | P1 | `/data` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | global badge, `/`, `/data`, preflight banner |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | `/data`, `/scanner-runs/<new id>`, global badge |
| UT-J-06 | Every page loads within budget | regression | P1 | 11 listed routes |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | global badge, `/backtest`, `/data` |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest`, `/data` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | global badge, `/backtest`, `/data` |

**All 8 test cases are P1** — every journey in this table is named on this iteration's
`Required-still-passing journeys:` line (J-01, J-03, J-04, J-06, J-08, J-09) or its `Target journeys:`
line (J-05, J-07); per the phase's own Definition of Done, none may merge as clean `SKIPPED`/`PASS`
without fresh, non-carried-forward evidence this iteration, and TC-11 requires a unique, checksum-distinct
evidence screenshot per journey — no two journeys sharing one file.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in this
plan, consistent with `Frontend Present: no`, zero changed files under `apps/frontend/`, and "New
user-facing capability: None".

**Two test cases carry an explicit KNOWN OPEN RISK flag this iteration (UT-J-05 steps 4/8-9; UT-J-07
steps 3/7-8; UT-J-08 step 6; UT-J-09 step 7)** — all trace to the SAME disclosed, unfixed-by-design
limitation: the append-forward fast path shipped this iteration does not accelerate historical gap-fills,
and every currently-available backfill target in this DB IS a historical gap-fill. Whoever executes this
plan should treat UT-J-05's actual measured elapsed time as the single highest-value piece of evidence in
the whole document, and report the actual number observed rather than a rounded pass/fail impression —
this is also the exact judgment call the reviewer's own review report defers to QA/the evaluator.
