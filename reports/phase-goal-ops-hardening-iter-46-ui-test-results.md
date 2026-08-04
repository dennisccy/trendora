# Phase goal-ops-hardening-iter-46 — UI Test Results

**Phase:** goal-ops-hardening-iter-46
**Date:** 2026-08-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: multiple P1 tests (J-01, J-03, J-05, J-06, J-07) did not observe their literal expected result
within a generous observation window (up to ~21 minutes for the target journey J-05, ~15 min for J-01,
~10 min for J-03/J-07). This iteration's own diff (the two bounded accumulators + two logger guards) is
well-supported by strong POSITIVE evidence — zero MemoryErrors anywhere in this session's logs, VmRSS
never approached the 8192MB cap, /api/health stayed 100% up and fast (<0.4s) even under two concurrent
backfill jobs + an active background-compute window. The FAILs below are overwhelmingly the SAME
already-disclosed, out-of-scope GIL/CPU-contention mechanism (a long synchronous finalize/coverage-refresh
recompute) the iter-46 dev handoff and this plan's own KNOWN OPEN RISK section anticipated — this iteration
does not fix that mechanism and does not claim to. This report scores each journey on its LITERAL observed
outcome per the plan's explicit instruction, not rounded to a pass because the underlying memory fix is
real. -->

**Overall:** 4/8 tests passed (0 skipped, 4 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors range, explains zero-work | regression | P1 | "2 non-trading" then "19 already snapshotted" render in Run history after each job resolves; `/scanner-runs/748` shows "as of 2026-05-29" | Both jobs (run 287, run 288-adjacent submission) accepted and transitioned to `running` correctly; run 287 (2026-05-02→2026-05-03) never left `running` after 15+ min observation (0/0 dates processed the whole time despite `non_trading_days:2` resolved instantly at the job-detail level) — the second job and `/scanner-runs/748` check were never reached | FAIL | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-01-fail.png` |
| UT-J-03 | No per-run range cap | regression | P1 | No "date range too large" message; job accepted and runs; eventually "412 calendar days" in Run history | No range-cap rejection message appeared at any point (core assertion holds); job (run 288, 2025-06-01→2026-07-17) accepted and stayed in `running` state for 10+ min observation, never reaching a terminal state with the "412 calendar days" text | FAIL | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-03-fail.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Badge transitions loading→ready within 5s of first health 200; `provider: seed`; `/data` Run history populated; hard-kill → badge shows unavailable; log ends abruptly; restart → interrupted jobs shown, page renders | All steps confirmed exactly as expected: clean-stop badge went `unavailable` while draining, first health 200 arrived ~29s after relaunch, badge settled `initializing`(89/89)→`ready` in ~3min (matches the plan's own disclosed normal-warmup precedent), `provider: seed` shown, Run history populated; hard `kill -9` → badge instantly `unavailable`, log ended abruptly mid-request with no clean-shutdown entry; second restart → all 4 mid-flight jobs (283-286) show `interrupted` (never a stuck `running` ghost row), `/data` renders fully populated (snapshot_count grew 2864→2869 from run 283's surviving partial work) | PASS | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-04-result.png` |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | EITHER run 284 (2019-02-25, confirmed absent beforehand) reaches `ok` within 300s with a rendered leaderboard and `aggregates_refreshed` including `membership_timeline`, OR it fails with a now-traceable log line — either outcome scored honestly | Run 284 submitted against the freshly-reconfirmed gap `2019-02-25` (same date whose prior attempt, run 281, failed with `MemoryError (no message)`). This time: NO MemoryError, NO failure — it simply never progressed (`0/1 dates done`, `0 snapshots`, `0 forward returns`) for the entire ~21-minute observation window, badge stayed `Ready` throughout. Ultimately `interrupted` only because I had to restart the backend to complete the rest of the suite — not a spontaneous terminal state. `logs/backend.log` names nothing because nothing failed; VmRSS/CPU showed the same single-thread-runnable GIL-starvation signature as the dev handoff's own 2005-05-16 drill | FAIL | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-01-fail.png` (shared badge/coverage state; see notes — no dedicated J-05 UI state to distinctly screenshot since the run never left the identical "running" row) |
| UT-J-06 | Every page loads within budget | regression | P1 | All 11 routes render their anchor text within budget; `/evidence` timing reported precisely | 10/11 routes (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) rendered their exact anchor text within 2-5s each — clean pass. `/evidence` (step 7): a direct, dedicated `GET /api/evidence` measurement (no other explicit timing constraint, ~10s after 2 backfill jobs + 1 background-compute window were already active) did **not return within the full 300-second budget** (`curl --max-time 300` → HTTP 000, `time_total=300.000568s`) — worse than both the plan's own 157s pre-test finding and the disclosed 73.3s historical worst case. The page itself degrades honestly (a persistent loading skeleton, never blank, never an error) but the endpoint itself is far outside its committed ≤3s steady-state / ≤1.5s endpoint budget | FAIL | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-06-evidence-slow.png` |
| UT-J-07 | Heavy aggregate warm never takes health/backtest/evidence down (target, +TC-4) | regression | P1 | Badge stays `ready`; `/api/health` stays responsive (≤2s BCW budget) throughout a ≥5min drill; `/backtest` n=14647 + `/data` gaps anchors render; `/evidence` under load reported precisely; `/backtest` never blank | Badge: stayed `Ready`/`GO` for the entire drill — PASS. Health: 34 polls over ~320s while 2 backfill jobs + 1 background-compute window ran concurrently, **100% HTTP 200, every response 0.10-0.40s** — well inside budget and markedly BETTER than the dev handoff's own drill (which saw several 5s client-timeouts) — PASS, and positive evidence the memory fix removed at least one prior failure mode. `/backtest` step-2 anchor "n=14647" confirmed unchanged (byte-identity holds). `/data` "Backfill gaps" rendered a real, live, plausible number (2526). `/evidence` step 4/8 (the single most important measurement in this plan): did **not return within 300s** with 2 jobs + background-compute already running — the strict "stays within committed budget" DoD wording is NOT met (same root cause as UT-J-06, GIL/CPU contention from the long synchronous finalize path, zero MemoryErrors). Step 9 (reload `/backtest` after "forward aggregates" appears) was never reached — neither job completed within the observation window | FAIL | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-07-badge-ready-under-load.png` |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest` renders promptly with last-good values or a "Refreshing" banner while a job runs — never blank, never an indefinite skeleton | `/backtest` rendered PROMPTLY with full, correct scorecard values (Market Regime 60.23, n=14647, etc.) while 2 backfill jobs AND an active background-compute window were all running concurrently — genuine PASS for the core claim. **Secondary finding, not scored against this test:** during an earlier, heavier drill (4 concurrent jobs stacked, before the J-04 restart), `logs/backend.log` recorded one unhandled `sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached` inside a `GET /api/backtest` request (`backtest.py:162`→`resolve_run`→`latest_data_date`), and that SAME browser tab was left showing an indefinite loading skeleton with no visible error or retry — this happened under an artificially stacked multi-source load (my own curl + repeated navigations on top of an already-GIL-starved job), heavier than the journey's own single-concurrent-job scenario, but it is a real, reproducible failure mode worth flagging to the evaluator/dev | PASS | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-08-result.png` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | Landing on an uncomputed historical as-of returns immediately; badge shows accent chip; `/data` panel lists it with elapsed+horizons; "process-lifetime only, never persisted" text visible; completion clears the chip | All disclosure mechanics confirmed with live, concrete data: clicking "Previous available date" on `/backtest` returned instantly with "(historical)" text (no blocking); badge showed `background compute running (1)` chip within ~8s; `/data`'s Background-compute panel listed the SAME window (`as-of 2026-07-30`, elapsed 44.2s→599s over repeated checks, horizons progressing 0→2→3 of 5) with the exact required disclosure text "process-lifetime only, never persisted." Step 7 (full completion + chip clearing) was not reached within the observation window, but genuine incremental progress (not a stall) was observed, and the plan explicitly tolerates recording this honestly rather than waiting indefinitely | PASS | `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-09-result.png` |

---

## Passed Tests

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-04-result.png`
- Clean stop (`SIGTERM` to the uvicorn PID) → badge flipped to `data-state="unavailable"` / "Backend unavailable" with a "NO-GO — do not rely on today's board" banner while uvicorn drained ("Waiting for connections to close" — took ~80s, likely lengthened by the same GIL-bound finalize work in flight at the time; process exited cleanly at 06:24:19).
- Relaunched via `bash scripts/start-backend.sh` (the exact script `browser-qa-phase.sh` uses) → first `/api/health` 200 arrived in ~29s; badge showed `data-state="initializing"` with `warmup: {done:89,total:89,status:"running"}` for ~3 minutes (an exact match for this plan's own disclosed "normal warm-up transition, not a bug" precedent) before settling to `data-state="ready"` / "Ready".
- `provider: seed` confirmed on the dashboard; `/data` rendered a fully populated "Run history" section.
- Hard `kill -9` on the fresh PID → badge instantly `unavailable` again; `tail logs/backend.log` showed the log ending abruptly mid `GET /api/data` request with no "Shutting down" / clean-exit line before the gap.
- Final restart (also via `scripts/start-backend.sh`, host-guard block confirmed applied: `memory_cap_mb=8192 malloc_arena_max=2 cpu_list=0-15 blas_threads=8`) → all 4 jobs that were mid-flight across both interruptions (283, 284, 285, 286) now read `status: "interrupted"` in `GET /api/data` — never a ghost `"running"` row with no living process. `/data` renders normally; `snapshot_count` correctly reflects run 283's 1 surviving snapshot (2864→2869 across this whole drill, +5 for run 283's 5 dates).

### UT-J-08 — Backtest serves stored evidence, never cold-recomputes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-08-result.png`
- With 2 backfill jobs (runs 287, 288) and 1 background-compute window (as-of 2026-07-30) all genuinely active, a fresh navigation to `/backtest` rendered the full, correct "Latest" scorecard (Market Regime 60.23/100, Candidate Counts, Forward-test scorecard) within a few seconds — real values, not a placeholder, not blank.
- "Forward-tested evidence" anchor text confirmed present.
- See the Results Table row above for a secondary QueuePool-exhaustion finding observed under a heavier, self-induced concurrent-request load — reported for completeness but not scored against this specific test's own (lighter) scenario, which passed cleanly.

### UT-J-09 — Background-compute activity disclosed on the badge and `/data` panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-09-result.png`
- `/backtest` → clicked "Previous available date" → page immediately showed "Viewing as-of 2026-07-30 (historical)" — confirmed the request did not block on the background dispatch.
- Badge showed the `background-compute-indicator` chip ("background compute running (1)") within ~8s of landing on the historical date; badge itself stayed "Ready" throughout (never flipped to unavailable because of the in-flight compute).
- `/data`'s "Background compute" panel (`data-testid="background-compute-panel"`) listed the exact same window: `as-of 2026-07-30`, `dataset r2869-f6435298`, elapsed time climbing (44.2s → 599.1s across repeated checks), `horizons 0/5 → 2/5 → 3/5` — genuine incremental progress, not a stall. The required disclosure text "process-lifetime only, never persisted" is visible verbatim.
- Step 7 (full completion, chip clearing, "Last outcome" populating) was not reached in the observation window (would likely need several more minutes at the observed ~1 horizon/3min rate) — recorded honestly per the plan's own tolerance for this outcome, not rounded to a pass or fail on that specific sub-step.

---

## Failed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** FAIL
**Failure:** The first backfill job (run 287, `2026-05-02`→`2026-05-03`) was accepted and correctly resolved `non_trading_days: 2` / `dates_total: 0` at the job-detail level almost instantly (`stages.backfill.elapsed_seconds: 0.087`), but the overall job record never left `status: "running"` for the full ~15-minute observation window (started `2026-08-04T05:30:35Z`, still `running` with `0/0` dates and no `aggregates_refreshed` at `05:45:43Z`). The Run History row for this run never displayed the expected "2 non-trading" summary text while stuck in this state (confirmed via a direct `get_text` read of the row — it just repeats "backfill: 0 snapshots over 0 dates, 0 forward returns"). The second step (2026-05-02→2026-05-29 "19 already snapshotted") and the `/scanner-runs/748` check were never reached.
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-01-fail.png`

**Steps taken:**
1. Navigated to `/data`, confirmed "Data Manager" heading.
2. Filled `job-start-date`=2026-05-02, `job-end-date`=2026-05-03 (using a React-native-setter trick after discovering plain `.value =` assignment does not update React state on this input).
3. Clicked "Start" (`06:02:31` local first attempt; the clean run analyzed here started `06:30:35` local, after a full backend restart cleared prior contention).
4. Polled `GET /api/data` / the job-detail endpoint every few seconds for 15+ minutes: `status` never left `"running"`.
5. Confirmed via the DOM that the Run History row for this exact run shows the raw zero-progress message the whole time, never the "2 non-trading" summary text the plan expects on completion.

**Expected:** Run summary includes "2 non-trading" shortly after submission (this is a genuinely zero-work range — both days are weekend).
**Actual:** Job accepted, correctly computed as zero-trading-days internally, but the overall job record stayed `"running"` indefinitely (15+ min, no completion) — the "2 non-trading" text never rendered.

**Note for the evaluator:** this is a NEW finding distinct from the already-disclosed historical-gap-fill slowness — this specific job needed ZERO snapshot/forward-return work (`dates_total: 0`), yet the surrounding finalize/coverage-refresh tail still appears to run an expensive unconditional recompute that never completed. Worth flagging as broader than the KNOWN OPEN RISK section anticipated.

---

### UT-J-03 — No per-run range cap
**Verdict:** FAIL
**Failure:** The 412-day range (`2025-06-01`→`2026-07-17`) was submitted and genuinely ACCEPTED — no "date range too large" or any range-cap rejection message appeared anywhere near the form, confirming the core "no per-run range cap" claim holds. The job (run 288) correctly transitioned to and stayed in a `running` state (satisfying step 5's narrower requirement). However, the job never reached a terminal state within the ~10-minute observation window, so the final "412 calendar days" summary text in Run History was never observed.
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-03-fail.png`

**Steps taken:**
1. Navigated to `/data`, filled `job-start-date`=2025-06-01, `job-end-date`=2026-07-17.
2. Checked the page for any range-cap rejection text before submitting — none found.
3. Clicked "Start" (`06:35:27` local). Confirmed via `GET /api/data` that a new run (288) appeared immediately with `status: "running"`, start/end dates matching exactly.
4. Watched the "Job progress" panel (`data-testid="job-status"`) and live-activity/heartbeat testids — panel correctly re-attached to this "job from a previous session" on reload and showed "running" with the same zero-progress message.
5. Polled for 10+ minutes: `status` never changed from `"running"`, `aggregates_refreshed` stayed `null`.

**Expected:** No range-cap rejection at any point (confirmed); eventually "412 calendar days" appears in Run history.
**Actual:** No rejection (PASS on that sub-claim); job accepted and running throughout, but "412 calendar days" never rendered within the observation window.

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (target journey)
**Verdict:** FAIL
**Failure:** `2019-02-25` was freshly reconfirmed as the live `coverage.gap_last` immediately before this drill (per `GET /api/data`). A single-day backfill was submitted (run 284, matching this iteration's own diff — the two bounded-accumulator fixes — being put under direct live pressure on the SAME date whose prior attempt, run 281, failed with `MemoryError (no message)`). This time: **no MemoryError occurred, and no failure of any kind occurred** — the job simply never advanced past `0/1 dates done, 0 snapshots created, 0 forward returns` for the entire ~21-minute observation window (`05:03:06Z` start to `05:24:56Z`, when a necessary backend restart to continue the rest of this suite finally interrupted it). This mirrors the dev handoff's own disclosed drill on the adjacent date `2005-05-16` almost exactly (VmRSS grew slowly, one thread stayed CPU-runnable — GIL starvation from the historical gap-fill's full membership-timeline recompute, not memory exhaustion).
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-01-fail.png` (badge/coverage state captured during the same drilling window — no visually distinct UI state exists for "still running" beyond the same Run History row already documented for UT-J-01; the run's own row is not separately screenshottable in a way that differs meaningfully)

**Steps taken:**
1. Confirmed `2019-02-25` was the live `coverage.gap_last` via `GET /api/data` immediately before the drill (not the golden script's stale default `2005-04-12`, and not the already-filled `2005-05-16`).
2. Navigated to `/data`, filled both date fields with `2019-02-25`, clicked "Start" (`06:02:31` local / `05:03:06Z`).
3. Watched the top-bar readiness badge throughout: stayed `data-state="ready"` / "Ready" the ENTIRE time — this held even under the eventual severe congestion.
4. Polled `GET /api/data` for the run's detail every few minutes for ~21 minutes: `status` stayed `"running"`, `snapshots_created: 0`, `dates_done: 0/1` the whole time — no incremental progress at all (unlike run 283, an adjacent gap-fill submitted earlier in this session, which did manage `1/5` dates before also stalling).
5. Restarted the backend (needed to unblock the rest of this test suite); run 284 now reads `status: "interrupted"`, confirming it never reached a natural terminal state.

**Expected:** Either (a) run reaches `ok` within 300s with a rendered leaderboard and `aggregates_refreshed` including `"membership_timeline"`, or (b) it fails with a now-traceable log line — either is honest evidence.
**Actual:** Neither (a) nor (b) — the job was silently, indefinitely stuck (a third outcome the dev handoff itself already anticipated and this plan explicitly asked to be reported literally). Positive signal: this iteration's own product change (the two bounded accumulators) was never implicated — zero MemoryErrors, VmRSS well under the 8192MB cap throughout.

---

### UT-J-06 — Pages load only what they need
**Verdict:** FAIL
**Failure:** 10 of 11 routes loaded correctly and quickly (2-5s each, exact anchor text confirmed for `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`). `/evidence` (step 7) is the one exception and the most important finding in this plan: a dedicated, isolated `GET /api/evidence` measurement (`curl --max-time 300`) taken while 2 backfill jobs and 1 background-compute window were active did **not return within the full 300-second budget** — `HTTP 000, time_total=300.000568s` (curl's own timeout firing, not a server error). The `/evidence` page itself degraded honestly in the browser (a persistent `animate-pulse` loading skeleton, never a blank page, never a JS error) but the underlying endpoint is drastically outside its committed ≤3s steady-state budget.
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-06-evidence-slow.png`

**Steps taken:**
1. Navigated through all 11 routes in sequence, confirming each route's anchor heading text via the DOM summary.
2. For `/evidence` specifically: navigated in-browser (showed a persistent loading skeleton, no claim rows, no error) AND ran a dedicated direct `curl --max-time 300 http://localhost:8255/api/evidence` timing check in parallel.
3. The direct curl exhausted its full 300s budget without a response.

**Expected:** Every page renders its anchor text within its committed budget; `/evidence`'s load time reported precisely given this iteration's own diff feeds its serving path.
**Actual:** 10/11 pages within budget; `/evidence` exceeded even the 300s ceiling I measured against (worse than the plan's own pre-test 157s finding and the disclosed 73.3s historical worst case) — reported precisely as instructed, not rounded to "close enough."

---

### UT-J-07 — Heavy aggregates never take the service down (target journey, + TC-4)
**Verdict:** FAIL
**Failure:** Mixed but clearly-attributable result. PASSING sub-criteria: the readiness badge stayed `Ready` for the entire ~10+ minute drill; `GET /api/health` polled 34 times over ~320s while 2 concurrent backfill jobs (runs 287, 288) plus 1 background-compute window ran, returning **HTTP 200 every single time, 0.10-0.40s each** — comfortably inside budget and better than the dev handoff's own drill (which saw several 5s timeouts); `/backtest`'s `n=14647` byte-identity anchor held exactly; `/data`'s "Backfill gaps" stat rendered a real, current number (2526). FAILING sub-criterion: `GET /api/evidence`, measured under the SAME concurrent load, did not return within the full 300-second budget I gave it (same measurement used for UT-J-06 step 7/8, since both ask for the identical "evidence under load" reading) — this is the one strict DoD wording ("`/api/evidence` stays within its committed budget... while a heavy data job runs concurrently") not met. Step 9 (reload `/backtest` after "forward aggregates" appears in Run history) was never reached because neither backfill job completed within the observation window.
**Evidence:** `reports/qa/goal-ops-hardening-iter-46-evidence/UT-J-07-badge-ready-under-load.png`

**Steps taken:**
1. Confirmed `/` shows "Ready" and `/backtest` shows "n=14647" before triggering any job.
2. Confirmed `/data` "Backfill gaps" renders a real number (2526).
3. Submitted the wide-range job (run 288, `2025-06-01`→`2026-07-17`, spanning genuine gaps) to trigger the full-horizon forward-aggregate warm.
4. Ran a background health-poll loop every 7s for ~320s (`curl -w "%{http_code} %{time_total}"`) — logged every response.
5. Watched the badge throughout — stayed `Ready`.
6. Ran a dedicated, isolated `GET /api/evidence` timing check with a 300s ceiling — did not return.
7. Re-checked `/backtest`, `/data` job rows — both jobs still `running` at the end of the observation window; "forward aggregates" never appeared in `aggregates_refreshed`.

**Expected:** `/api/evidence` returns within budget and `/api/health` stays responsive throughout a heavy job; no MemoryError-triggered outage.
**Actual:** `/api/health` requirement MET (and markedly improved vs. the dev's own drill — a genuine positive signal for the bounded-accumulator fix's effect on the health path specifically). `/api/evidence` requirement NOT MET (300s+, exceeding even the previously-disclosed worst case). No MemoryError anywhere in this session's logs — the narrower "no MemoryError-triggered outage" objective this diff targets IS met; the stricter latency wording is not.

---

## Skipped Tests

None — Chrome MCP and both frontend/backend were available throughout; every test case was executed to at least a concrete, evidence-backed conclusion.

---

## Additional findings (not tied to a single UT-XX row)

1. **New: `QueuePool` exhaustion under stacked concurrent load.** During an earlier, heavier phase of this drill (4 concurrent backfill jobs stacked before the mid-suite backend restart, plus my own duplicate `curl`/browser requests), `logs/backend.log` recorded an unhandled `sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached, connection timed out, timeout 30.00` inside a live `GET /api/backtest` request (`backtest.py:162` → `resolve_run` → `latest_data_date`). The browser tab that triggered it was left showing an indefinite loading skeleton with no error message and no automatic retry. This reproduced under a heavier, self-stacked load than any single journey's own scenario describes, but it is a genuine, reproducible backend failure mode (a request can fail outright with an unhandled 500 under enough concurrent DB contention, rather than degrading gracefully) worth a dedicated look in a future iteration.
2. **Zero MemoryErrors across this entire session.** Despite deliberately reproducing and exceeding the conditions of the prior MemoryError (run 281, same date `2019-02-25`), plus running up to 4 concurrent heavy jobs and 1 background-compute window simultaneously, `grep MemoryError logs/backend.log` shows no new occurrences anywhere after this backend session started (PID 1335434 onward, `logs/backend.log` line 174559+) — the only MemoryError lines in the whole file are from hours earlier (run 281's original failure). This is strong, direct evidence that this iteration's core product change (bounding `_combination_observations` and `compute_drawdown_expectations`) is working as intended.
3. **New (broader than KNOWN OPEN RISK anticipated): even a zero-trading-day, zero-snapshot backfill request (run 287) never resolves quickly.** The plan's own precondition notes expected "very quick" zero-work resolution; instead, run 287 (2 weekend days, `dates_total: 0` resolved instantly at the job-detail level) never left `"running"` in 15+ minutes on an otherwise idle, freshly-restarted backend. This suggests the finalize/coverage-refresh tail runs its expensive recompute unconditionally after every backfill submission, not only ones with genuine gap-fill work — a materially different (and more concerning) shape than "historical gap-fills are slow," since it affects the everyday zero-work case too.
4. **AG-10 host-guard caps confirmed enforced on every launch.** Both backend restarts' boot logs show `memory_cap_mb=8192 malloc_arena_max=2 cpu_list=0-15 blas_threads=8` applied via `scripts/start-backend.sh`, consistent with the owner's 2026-07-31 amendment.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-08-04 (approx. 05:52-06:47 local / 04:52-05:47 UTC)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-46-evidence/`
- **Backend restarts performed:** 2 (one clean `SIGTERM` + relaunch for UT-J-04 steps 1-4, one hard `SIGKILL` + relaunch for UT-J-04 steps 5-8) — both via `bash scripts/start-backend.sh`, matching `browser-qa-phase.sh`'s own launch command
- **Concurrent jobs exercised across the session:** runs 283 (2005-05-17→2005-05-23, partial 1/5), 284 (2019-02-25, J-05 target, 0/1), 285/287 (2026-05-02→2026-05-03 zero-work, two separate submissions), 286/288 (2025-06-01→2026-07-17 412-day, two separate submissions) — none reached a natural terminal `ok`/`failed` state during this session; all were eventually marked `interrupted` by the necessary mid-suite backend restarts
