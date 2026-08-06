# Phase goal-ops-hardening-iter-50 — UI Test Results

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/10 tests passed (2 skipped) — but UT-03 (P1) FAILED with a critical finding: the backend
became completely unresponsive to `GET /api/health` for 12+ continuous minutes (and counting, as of the
end of this QA session) during a live ingest job's finalize tail, which is the exact scenario this iteration
was built to make safe.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab loads without errors | smoke | P1 | Heading + populated all-factors table, real rank-IC/forward-return figures, no console 500s | Page loaded, heading "Research — Factor Lab" present, `factors-table` rendered 11 rows with real rank-IC/decile figures on a warm cache (163ms API call) | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-01-result.png` |
| UT-02 | Historical-day backfill reaches terminal status | happy-path | P1 | Job reaches terminal status ≤20min, scanner-runs row + leaderboard render | Backfill for `2012-01-04` reached `status: "ok"` in 11m16s (21:52:45→22:04:01 UTC), `aggregates_refreshed` included `membership_timeline`; `/api/runs` confirmed the date present (2908 rows). The "within ~30 seconds" aggregates-line sub-claim did NOT hold (see note) | PASS (with note) | API responses (see Notes); no final UI screenshot of the scanner-runs leaderboard was captured — see Notes |
| UT-03 | Factor Lab survives a concurrent finalize-tail warm | error | P1 | Readiness stays `ready` throughout; Factor Lab loads every time; no crash/hang | **Backend became fully unresponsive to `GET /api/health` for 12m03s+ (confirmed continuously, still ongoing when this report was written) during a second ingest job's finalize tail. The browser's readiness badge stayed stuck on "Checking backend…" (never `ready`, never even `unavailable`) for 17m+ straight. Process never crashed (still running, CPU-busy, `futex_do_wait`) but the service was not serving ANY request, including `/api/health`.** | **FAIL** | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-03-fail.png` |
| UT-04 | Job form blocks incomplete date range | validation | P3 | Start button stays disabled when start date is empty | Start-date field emptied, end-date set to `2012-01-06`, Start button `disabled=true` confirmed via DOM | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-04-result.png` |
| UT-05 | Evidence drawdown-expectations panel still renders | regression | P2 | Table renders real percentage/numeric rows, not the unavailable fallback | `evidence-expectations-table` rendered 5 rows with real figures (e.g. "-7.42% (p90 -3.65%) n=362642") for the regime claim card | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-05-result.png` |
| UT-06 | Backtest scorecard still renders | regression | P2 | Scorecard shows real numeric hit-rate/mean-return figures, Leadership cohorts populated | At the default "Latest" as-of, every horizon showed honest NA (n=0) — correct behavior, no elapsed forward window yet, not a defect. Selecting a historical as-of (`2026-04-01`) showed a full real scorecard (hit rate 59.18%, mean +0.26%, populated sector/theme/ticker leadership tables) | PASS (see note) | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-06-result.png` |
| UT-07 | Background-compute panel still renders | regression | P2 | Idle OR populated active-row state, never blank | `background-compute-active-row` rendered with real as-of (`2026-04-01`), elapsed (18.6s), horizons (0/5), dataset version | PASS | `reports/qa/goal-ops-hardening-iter-50-evidence/UT-07-result.png` |
| UT-08 | Degraded Factor Lab response reuses empty-state | ux | P3 | N/A (advanced, requires backend restart) | Not attempted — see Skipped section | SKIP | none |
| UT-09 | Cold restart renders coverage within budget | regression | P2 | N/A (advanced, requires backend restart) | Not attempted — see Skipped section | SKIP | none |
| UT-10 | Factor Lab page-load timing measured | ux | P2 | First live measurement recorded; warm load feels responsive (low single-digit seconds) | Warm/cached load: nav 52ms, API call 163ms, table (11 rows) rendered essentially instantly — well within budget. Separately (diagnostic, not part of the formal timing claim), two COLD cache-miss computations of the same endpoint took 780s and 875s (13–14.6 min) — see Notes | PASS (with finding) | timings recorded in Notes / `reports/perf-budgets.md` Addendum 8 |

---

## Passed Tests

### UT-01 — Factor Lab loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-01-result.png`
- Navigated to `/research/factor-lab` on a warm cache; heading "Research — Factor Lab" rendered; `[data-testid=factors-table]` had 11 `tbody` rows with real, non-placeholder rank-IC/decile percentage figures (e.g. "Downside volatility (semivol)... +0.45% +1.12% +2.16%..."). No error card, no blank screen. (Note: an EARLIER attempt at this same navigation, made before the endpoint's cache was warm, never resolved after 4m20s of waiting — see the "Diagnostic detour" note below; the page itself was not defective, the endpoint was genuinely mid cold-compute / competing with a redundant concurrent request I had issued via curl.)

### UT-02 — Historical-day backfill reaches a terminal status
**Verdict:** PASS
**Evidence:** API-level (see note on missing UI screenshot)
- Verified live, before starting, that `2012-01-04` had 0 rows in `/api/runs` (2907 total runs at the time).
- Filled `job-start-date`/`job-end-date` = `2012-01-04`, confirmed "Job kind" = `backfill` (default, untouched), clicked Start.
- Immediately after: `data-testid="job-status"` showed the spinning icon (`animate-spin`) and text "running" — confirmed via DOM.
- The job reached `status: "ok"` at `2026-08-05T22:04:01Z` (started `21:52:45Z`, total 11m16s — within the 15–20 minute budget), with `snapshots_created: 1`, `forward_returns_inserted: 1430`, `dates_done: 1/1`.
- `aggregates_refreshed` on completion: `["latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]` — mentions "membership_timeline" as required, but is missing `drawdown_expectations`. This is consistent with the NEW warm-in-progress guard causing a one-time defer (the dev handoff itself documents this as an expected, rare, honest outcome, not a bug) — I did not independently confirm whether the deferral happened via the guard vs. some other cause, since I could not read backend logs from that exact window (they have since scrolled past during my later, much longer session).
- `GET /api/runs` (queried directly) confirmed `2012-01-04` present (2908 total rows) — the API-level equivalent of the "row appears on `/scanner-runs`" assertion.
- **Note (test-plan timing inaccuracy, not a product defect):** the plan's "within ~30 seconds" expectation for the `aggregates-refreshed` line to appear did NOT hold — I confirmed via the live job API that `aggregates_refreshed` was still `[]` at t=189s (backfill sub-stage done) and only populated once the ENTIRE finalize tail completed (~11 minutes in). This matches the iteration's own stated design (aggregates are refreshed only once the whole finalize tail completes) and contradicts only the test plan's own pacing assumption — worth a plan correction, not a code fix.
- **Note (evidence gap):** I did not capture a UI screenshot of the `/scanner-runs` row + leaderboard detail page for `2012-01-04` specifically. My first attempt (before the finalize tail even started) found the row not yet present (correct, job still running); my second attempt (after the job completed) hit a very long, unpaginated 2908-row list with no search/jump control for a date this old, and before I could resolve it I moved to UT-03's setup; by the time I returned, the backend had entered the hung state documented in UT-03 below. I rely on the direct API confirmation (`2012-01-04` present in `/api/runs`) as the evidentiary basis for PASS.

### UT-04 — Job form blocks Start with an incomplete date range
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-04-result.png`
- Cleared `job-start-date` to empty, typed `2012-01-06` into `job-end-date`. Confirmed via DOM: `job-start-date.value === ""`, `job-end-date.value === "2012-01-06"`, Start button `disabled === true`. No job started.

### UT-05 — Evidence page's drawdown-expectations panel still renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-05-result.png`
- Navigated to `/evidence`, found a card with `data-testid="evidence-claim-regime"`, confirmed its `data-testid="evidence-expectations-table"` (not the `-unavailable` fallback) rendered 5 rows with real percentage/sample-size figures (e.g. "Expansion -7.42% (p90 -3.65%) n=362642").

### UT-06 — Backtest page still renders forward-test scorecard numbers correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-06-result.png`
- At the true default ("Latest," `2026-08-03`), every horizon in the Forward-test scorecard correctly showed honest NA (`—`, n=0) — expected behavior since that as-of has no elapsed forward window yet (the page says so explicitly: "No elapsed forward window for this date yet"). This is NOT a defect; it's the same honest-NA convention the whole product uses.
- Selected a historical as-of (`2026-04-01` via the calendar) and confirmed the scorecard populated with real figures across all horizons (e.g. 60d: +14.99% cohort / n=19), the Distribution & hit-rate panel (mean +0.26%, median +0.34%, hit rate 59.18%, n=539), and Leadership cohorts (Top Sectors/Themes with real tickers and forward returns).
- No error card, no blank screen, no console-500 evidence found (see tooling note below).

### UT-07 — Data page's background-compute panel still renders correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-07-result.png`
- Navigated to `/data`, found `data-testid="background-compute-panel"` with `background-compute-active-row` (not idle, since my UT-06 historical as-of view had just triggered a background compute) showing `as-of 2026-04-01`, `elapsed 18.6s`, `horizons 0/5`, real dataset version. Never blank, never an error boundary.

### UT-10 — `/research/factor-lab` page-load timing is measured
**Verdict:** PASS (with a notable finding)
**Evidence:** timing captured via the Performance API; recorded in `reports/perf-budgets.md` Addendum 8
- **Warm/cached measurement (clean, isolated, no concurrent job):** navigation duration 52ms; `GET /api/research/factor-lab?all=true` duration 163ms; the all-factors table (11 rows) was present essentially the instant the page settled. This is well within a "responsive, low-single-digit-seconds" experience.
- **Cold cache-miss finding (diagnostic, not part of the formal warm-load claim, but directly relevant to TC-12/perf-budgets):** two separate cold computations of the same endpoint (fired manually while investigating an unrelated question, see Notes) took **780.2s and 874.7s (13.0–14.6 minutes)** — both HTTP 200 with 11 real factors, no crash, no error. This is notably longer than the dev handoff's own documented "~2–4 minutes" cold-MISS range. I could not isolate whether this specific host's slower time is because two such computations were in flight back-to-back (competing for the same CPU-bound work) or because the true single-request cold cost is simply higher than the ~2–4 min figure on this data basis. Flagged as a finding either way.

---

## Failed Tests

### UT-03 — Factor Lab survives a concurrent finalize-tail warm; backend stays responsive (TC-1)
**Verdict:** FAIL
**Failure:** The backend's `/api/health` endpoint became completely unresponsive (no response at all — not even a slow one; repeated `curl --max-time 5..30` all returned connection code `000`, i.e. no response within the timeout) for a **continuous 12-minute-plus window** during a live ingest job's finalize tail, and was STILL unresponsive when I ended this QA session. The frontend's own readiness badge (`data-testid="readiness-badge"`) never advanced past `data-state="loading"` / "Checking backend…" for 17+ minutes straight — it never even reached the honest `unavailable` state the app is designed to show on a failed poll, because the poll's underlying `fetch()` never settled (the request itself hung, rather than erroring).
**Evidence:** `reports/qa/goal-ops-hardening-iter-50-evidence/UT-03-fail.png` (readiness badge stuck on "Checking backend…" at 2026-08-05T23:07:52Z, 17m+ into the hang)

**Steps taken:**
1. Verified `2013-02-14` had 0 rows in `/api/runs` (a second, fresh unsnapshotted date — the golden's original `2012-01-04` target had just been consumed by UT-02's own successful run).
2. Started a "Backfill snapshots" job for `2013-02-14` on `/data` (job_id `278ddb7d8cd3418fac93908b1b7e369b`, started `2026-08-05T22:32:52Z`).
3. Monitored the job via the live API while doing other independent tests (UT-05/UT-06/UT-07/UT-10) in the same browser tab.
4. Once the job's finalize tail was clearly deep in its heavy phases (`forward_aggregates_warm`, `research_hot_keys_warm`, `drawdown_expectations_warm` — logged phase timings of 22.6s–337.5s each), repeatedly checked `GET /api/health` (curl, 5–30s timeouts) and the browser's readiness badge.
5. `drawdown_expectations_warm` completed at `2026-08-05T22:57:06Z` (local backend-log clock; 314.38s for that phase alone), processing several claims including the already-documented-expensive `combination:composite:h20` claim (112.58s).
6. From that point (`22:57:06Z` backend-log time) onward, the backend log **stopped advancing entirely** and `GET /api/health` **never answered again** through the end of this QA session (last confirmed check: `2026-08-05T23:12:08Z` UTC — 15m02s of total silence, no new log line, no HTTP response of any kind).
7. Confirmed the process was still alive (`ps -p 1490890` showed it running, ~85–89% CPU, RSS actually DROPPED from 7.76GB to 5.89GB partway through — not an OOM kill), with its main thread parked in `futex_do_wait` — consistent with a genuine lock/wedge condition, not a crash.
8. Did NOT restart or kill the backend process (per instructions) — left it in this state at the end of the QA session.

**Expected:** The readiness badge stays `data-state="ready"` throughout; `/research/factor-lab` finishes loading every time it's opened; the concurrent ingest job's own progress is unaffected by opening Factor Lab. Per the phase's own framing, this is "this iteration's single most important test," with an explicit fail condition of "the readiness badge in the OTHER tab flips to `data-state="unavailable"` and stays there."
**Actual:** The badge never reached `ready`, `unavailable`, OR any resolved state — it stayed on the initial `loading`/"Checking backend…" placeholder indefinitely, because `GET /api/health` itself never returned any response (not a 5xx, not a slow 200 — a full connection-level non-response) for 12+ continuous minutes. This is a more severe symptom than the literal "flips to unavailable" fail condition describes (unavailable would at least be an honest, resolved signal); here the service is simply not answering at all.

**Important context for scoring:**
- The backend process itself did **not** crash — this is a real improvement over the prior round's actual process death. Multiple `MemoryError`s were logged during this same window and were each caught and degraded gracefully by the code's isolation convention (e.g. `"factor_lab_all_cached: compute_factor_lab_all aborted under memory pressure ... degrading the response honestly, not crashing"`), which is exactly this iteration's intended fix working as designed for **its own specific target** (`compute_factor_lab_all`'s per-(factor,horizon) loop).
- However, several of the `MemoryError`s I observed in the live log were **not** in that bounded code path — they were in `_all_factor_observations_by_horizon` (`research.py:964`/`966`) and `_combination_cohort_members` (`research.py:1326`/`1334`, reached via `samples.py:277`'s `_combination_samples`) — functions the phase spec explicitly says are "already bounded, iter-31/iter-52 work, unaffected by this defect" and out of scope for this iteration. They were still individually caught/degraded (no crash), but their repeated firing shows the underlying memory-pressure condition is broader than just the one function this iteration bounds.
- The specific multi-tens-of-seconds-to-minutes-per-phase blocking pattern (`forward_aggregates_warm` 337s total, `drawdown_expectations_warm` 314s total, with the `combination:composite:h20` claim alone costing 112.58s) matches the **already-documented, explicitly out-of-scope** "early/mid/late stall clusters" in `reports/perf-budgets.md` Item R Addendum 6/7 — carried forward from prior iterations, not newly introduced by this one's specific diff. The NEW finding here is not that these phases are slow (already known) but that the **total, sustained unresponsiveness this specific live run produced (12+ minutes and still not recovered) exceeds even the prior round's own 12m45s outage** that this whole iteration exists to prevent — regardless of which exact line of code is the proximate cause.
- I cannot fully rule out that my own earlier diagnostic use of the same endpoint (two manual, redundant ~13–15 minute `curl` calls to `compute_factor_lab_all`, made before I understood the endpoint's caching behavior — see Notes) left the process's memory allocator more fragmented/pressured than a single real user's page view would, making this specific run's memory pressure somewhat worse than the test's own prescribed single-concurrent-load scenario. I flag this honestly; it does not change the fact that the service ended this session in a genuinely unresponsive, unrecovered state.

---

## Skipped Tests

### UT-08 — A degraded Factor Lab response reuses the "empty" state (advanced/optional)
**Verdict:** SKIPPED
**Reason:** Requires restarting the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all` set, then restarting it again without that variable. Per my instructions, I do not restart or debug the app's services myself. Additionally, by the time I reached this test the backend had entered the unresponsive state documented in UT-03 — restarting it at that point would have destroyed the in-flight evidence of that finding and interrupted a live job. This is explicitly framed by the test plan as advanced/optional for a browser-only tester.

### UT-09 — Cold restart: `/data` renders from the persisted payload within budget (advanced/optional, TC-11)
**Verdict:** SKIPPED
**Reason:** Same as UT-08 — requires a backend restart, which I do not perform myself, and the backend was in the middle of the UT-03 finding (unresponsive, mid-job) by the time this test's preconditions would have been met.

---

## Notes for the evaluator

- **Diagnostic detour (own testing artifact, not a product finding):** early in this session, before understanding that `factor_lab_all_cached` uses a server-side cache, I fired two manual `curl` requests to `GET /api/research/factor-lab?all=true` (780s and 875s respectively) in parallel with my own browser navigation, to understand why a page load appeared stuck. This was diagnostic overreach beyond the test plan's prescribed steps, and it briefly caused unrelated endpoints (`/api/backtest`, even `/api/health`) to slow to 5–20s response times while those computations were in flight — this was self-inflicted contention, not a product finding, and it fully resolved (all endpoints back to sub-200ms) once both curls completed, well before UT-03's own test began. I mention it for transparency but did not let it affect any test's verdict.
- **UT-03 is unambiguously this iteration's most important result.** Whatever the precise root cause (DB write-lock contention, event-loop starvation from synchronous CPU-bound warm phases, the new warm-in-progress guard, or the pre-existing stall clusters compounding under additional memory pressure), the observed, measured fact is: a live ingest job's finalize tail left the whole service unable to answer `GET /api/health` for 12+ continuous minutes, unresolved as of the end of this QA session. This is the exact class of outage this iteration's `GOAL`/`DEFINITION OF DONE` targets, and it recurred.
- **Tooling limitation:** the Chrome MCP browser's console-message auto-capture reported "not yet implemented" throughout this session (`# TODO: Console logging not yet implemented`), so I could not directly confirm "no browser console errors mentioning a 500" via the automated capture path for any test. Where a page rendered its expected populated content with no visible error card, I treated that as sufficient positive evidence; this is a gap in the tooling, not something I can additionally verify with the tools available.
- The `journey-scripts/J-05.json` golden was rewritten to target `2010-11-08` (confirmed absent from `/api/runs` at the time of writing) since the previous golden's `2012-01-04` target was consumed by this run's own successful UT-02 backfill. Note for a future session: this golden's `wait_for: 15000` / `expect "1/1 dates"` step likely cannot complete within `demo_runner.py`'s hard per-step timeout in a real replay, since the live backfill sub-stage itself measured ~189s (not 15s) before `dates_done` reached 1 in this run — this mirrors the SAME structural issue iter-49 already logged for TC-1's own golden ("investigated and found infeasible… hard-capped 20,000ms per-step timeout"). I preserved the existing convention (this is how the prior golden was already shaped) rather than inventing a new one, but flag it so it isn't silently trusted.
- No golden replay scripts were written for J-06 or J-07 this round: J-07 is the journey UT-03 just failed (writing a "verified PASS" script for it would misrepresent the finding), and I did not complete a full, clean J-06 page-tour this session to justify overwriting its existing golden.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (became unresponsive from ~2026-08-05T22:57:06Z onward — see UT-03)
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-05
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-50-evidence/`
