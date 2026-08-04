# Phase goal-ops-hardening-iter-45 — UI Test Results

**Phase:** goal-ops-hardening-iter-45
**Date:** 2026-08-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: both target journeys (J-05, J-07), each P1, failed live browser/API verification this run. -->

**Overall:** 0/2 tests passed (0 skipped) — UT-J-05 and UT-J-07 are the only two rows this agent executed/emits, per the dispatch's goal-mode regression-lane instruction that J-01/J-03/J-04/J-06/J-08/J-09 were already re-verified by deterministic golden-script replay and must NOT be re-tested or re-emitted here (their rows merge in separately).

**Headline finding:** during this run's own execution of UT-J-05, the backend (`http://localhost:8255`) went from healthy (`200`, `readiness: ready`) into a **complete, extended, live wedge** — zero HTTP responses of any kind (TCP-level timeout, curl code `000`) to `/api/health` across **60+ consecutive polls spanning ~34 minutes** (`00:49:29Z`→`01:21:40Z`, still unresolved when this report was written). The backend process stayed alive (never crashed, never restarted by this agent) but stopped accepting new connections while its own background threads kept throwing `MemoryError` from the SAME two accumulators the phase spec's own "OUT OF SCOPE" section names as an already-disclosed, deliberately-deferred finding (`research.py:777`, `forward_testing.py:2343`). This is direct, live evidence against J-07's core acceptance ("GET /api/health stays responsive... never a deadlock, wedge, or restart requirement") and J-05's "badge stays ready throughout" clause — discovered organically, not manufactured by pushing the system harder than the test plan called for.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | Backfill of a confirmed-absent historical date (`2019-02-25`) reaches terminal `ok` with a rendered leaderboard within a bounded window; badge stays `ready` throughout | Job (run 281) reached terminal status **`failed`** at t≈4m46s with message `"MemoryError (no message)"` — no snapshot, no scanner run ever created for `2019-02-25`. Backend then became fully unresponsive for 34+ minutes (still ongoing); the readiness badge never reached "Ready" again during that window, stuck on "Checking backend…" instead | FAIL | `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png` |
| UT-J-07 | Heavy aggregates never take the service down (target) | regression | P1 | `GET /api/health` stays HTTP 200 throughout a heavy warm; badge stays `ready`; `/backtest` never blank/frozen | Steps 1/3 partially confirmed pre-outage (badge "Ready", "Backfill gaps" = **2532**, a plausible nearby value to the script's stale `2533` anchor — consistent with the plan's disclosed drift). Step 2 (`/backtest` "n=8991") was not independently re-checked before the outage began. Steps 4-8 could not be executed as scripted because the backend was **already unreachable** for the entire remaining observation window: 60+ consecutive `/api/health` polls over ~34 minutes all returned no response (curl code `000`, 8-60s timeouts) — a 0% pass rate on the health-polling requirement, not the expected 100% | FAIL | `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-07-fail.png` |

---

## Passed Tests

None this run.

---

## Failed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png` (Data Manager page stuck on "Checking backend…" / skeleton loaders, ~25 min into the outage)

**Steps taken (Chrome MCP + direct API polling, per coordinator's explicit permission to poll via curl in bounded foreground loops):**
1. Confirmed via `GET /api/data` that `coverage.gap_last = "2019-02-25"` — genuinely absent from `/scanner-runs` (not the golden script's stale `2005-04-12` default, which is already snapshotted as `id 1882`).
2. Navigated to `http://localhost:3255/data` — confirmed heading "Data Manager", readiness badge "Ready", "Backfill gaps" = 2532.
3. Set both "Start date" and "End date" (`data-testid="job-start-date"` / `job-end-date`) to `2019-02-25` (via a React-correct `HTMLInputElement.value` setter + `input` event — the raw `type` action appended into a pre-filled field rather than replacing it, a tool-technique note, not a product bug).
4. Clicked "Start" (`//button[@type='submit']` containing "Start"). Confirmed via `logs/backend.log` that the frontend began polling `GET /api/data/jobs/79867db8aeae4af89a9b2086fd58cb25` (200 OK) and via `GET /api/data` that a new run row `id=281` (`start=end=2019-02-25`, `status=running`) appeared. Start time: `2026-08-04T00:38:14.322361Z`.
5. Polled `GET /api/data` (for run 281's status) and `GET /api/health` every 15-20s. Badge/`readiness` stayed `"ready"` while the job ran; one pre-existing `background_compute.active` window (`asof_key=2026-07-30`) was independently observed advancing `horizons_done` 0→1 during this window.
6. At `2026-08-04T00:43:23Z` (≈5m9s after start, well under TC-4's 300s budget on elapsed time — but NOT the required outcome), run 281 reached terminal status: **`"failed"`**, `"message": "MemoryError (no message)"`, `finished_at: 2026-08-04T00:43:00.955185`. No snapshot was created (`snapshots_created: 0`), `aggregates_refreshed: null`. `GET /api/runs?limit=5` confirmed **no scanner run was ever created for `2019-02-25`** — the create-once scan stage itself never completed either, contradicting the plan's expectation that "the create-once scan stage itself... is UNCHANGED by this iteration and should resolve quickly."
7. Traced the failure in `logs/backend.log`: the exception was NOT caught by `_refresh_ingest_aggregates`'s own per-item `MemoryError` isolation handlers (which log `"...aborted — memory pressure, continuing..."` and keep going) — it propagated to the OUTER handler at `data_manager.py:4681-4693`, which sets `prog.status = "failed"` and `prog.message = f"{type(exc).__name__} (no message)"` (exactly the iter-44-added honesty fix — it worked correctly in the sense of not fabricating a message, but the underlying job still failed outright rather than completing).
8. Reloaded `http://localhost:3255/data` (~4 min after the failure) to check the Run History row and readiness badge for the required step 10/11 checks — the page **never finished loading**: it stayed on "Checking backend…" with skeleton placeholders indefinitely (screenshots taken at +13s, +30s, and again ~25 minutes later — all identical).
9. Diagnosed via `curl`/`ps`/`ss`: `GET /api/health` and `GET /api/data` both returned **zero response** (curl `000`, connection accepted into the kernel backlog per `ss -ltnp` showing `Recv-Q=8` but never serviced) across dozens of polls from `00:49:29Z` through `01:21:40Z` (final probe before writing this report) — **~34 minutes of continuous, unbroken unresponsiveness, still unresolved**. The backend process (`pid 855388`) was confirmed alive throughout (`ps`: `State: S`, RSS steady at 7.5-7.66 GB against its `memory_cap_mb=8192` ceiling, CPU 157-171%, 18-21 threads) and was actively still writing to `logs/backend.log` — a continuous stream of caught `MemoryError` tracebacks from `research.py:777` (`_combination_observations`' `ret_by_run_symbol` dict) and `forward_testing.py:2304/2343` (`compute_drawdown_expectations`' `stored_by_key` dict) — **the SAME two "unbounded evidence-path accumulators" the phase spec's own OUT OF SCOPE section explicitly names** ("iter-44/al's two unbounded evidence-path accumulators (`research.py:777`, `forward_testing.py:2343`) — a separate, real finding, deliberately not this iteration's second risky action").
10. The frontend server itself (port 3255) stayed independently healthy (`200` at `/`, 0.4s) throughout — only the backend (port 8255) was wedged. Per this agent's rules, the backend was **not** restarted or debugged to "fix" this — the outage was left exactly as encountered and reported literally.

**Expected:** Step 9's "Refreshed:" text reaches a terminal state (ideally "ok" with aggregates listed, or, per the disclosed risk, "still running" at the 20-minute mark) while the badge stays `ready`.

**Actual:** The job failed outright with an uncaught `MemoryError` in ~5 minutes (not a stall), no snapshot/scanner-run was ever produced, and the badge subsequently got stuck in a non-`ready`, non-`unavailable` limbo ("Checking backend…") for 34+ minutes as the whole backend became unreachable. This is a materially worse and different outcome than either of the two outcomes the test plan's KNOWN OPEN RISK section anticipated ("still running" or "reaches ok").

---

### UT-J-07 — Heavy aggregates never take the service down (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-07-fail.png` (same stuck "Checking backend…" `/data` state, captured at the end of the observation window for this journey's own citation)

**Steps taken:**
1. Step 1 (badge "Ready" at `/`) and step 3 ("Backfill gaps" panel) were confirmed **before** the outage began, at the very start of this session (`~00:37Z`): badge text "Ready", "Backfill gaps" = **2532** — a plausible nearby value to the script's stale `2533` anchor, exactly as the test plan's KNOWN OPEN RISK section anticipated (treated as a pass for "the panel renders a real number consistent with a very recently filled gap").
2. Step 2 (`/backtest` "n=8991") was **not independently re-checked** this run before the outage started — noted honestly rather than assumed.
3. Step 4 (trigger a new wide-range backfill, e.g. `2019-01-01`→`2019-02-25`) was **not attempted**: by the time UT-J-05's job (which itself is a subset of that same gap range) had failed and the backend wedged, the backend was no longer reachable to submit a new job through the UI.
4. Step 5 (poll `GET /api/health` at 1Hz-ish for 5+ minutes, log every response code + `time_total`) **was** executed, far exceeding the 5-minute minimum: 60+ polls spanning `00:49:29Z`→`01:21:40Z` (~34 minutes). **Result: 0 of 60+ polls returned HTTP 200** — every single one timed out with curl code `000` (no response at all, not merely a slow one) at timeouts ranging 8-60s.
5. Step 6 (watch the badge) — confirmed via repeated screenshots of `/data`: the badge stayed on "Checking backend…" for the entire window, never displaying "Ready" (nor the expected honest "Backend unavailable" fallback state described in J-04's acceptance text — a secondary, minor finding: the badge's health-poll fetch appears to hang rather than time out client-side and fail over to the explicit "unavailable" UI state).
6. Step 7 (open `/backtest` in a second tab while the job runs) — not attempted; opening any page against an unreachable backend would only reproduce the same hang already documented for `/data`, and a prior in-page `eval`/`fetch` probe against `/api/health` from within the browser itself also hung (`Runtime.evaluate` session timeout), consistent with the backend-level wedge rather than a frontend-specific bug.
7. Step 8 (reload `/backtest` after "forward aggregates" appears) — not reached; the triggering condition (step 4) was never reached.

**Expected:** Every `/api/health` poll returns HTTP 200 (per this iteration's own TC-6: "≤2s bounded-compute-window budget... never fully unreachable"); badge stays `ready`; `/backtest` renders promptly or shows the "Refreshing" banner, never blank/frozen indefinitely.

**Actual:** The backend was completely unreachable for the entire eligible observation window — a 0% health-check pass rate over ~34 minutes, well past both TC-6's per-poll budget and the "never fully unreachable" clause. This was observed as a side effect of UT-J-05's own (much smaller, single-day) backfill plus pre-existing background load, without this agent ever needing to submit UT-J-07's own larger triggering range — i.e., the failure condition J-07 exists to prevent occurred before J-07's own trigger step could even be attempted.

---

## Skipped Tests

None — both dispatched test cases were executed to a definitive, evidenced verdict (FAIL). No test was marked SKIPPED; the extended backend outage is reported as part of UT-J-05/UT-J-07's own FAIL evidence, not as a reason to skip.

Per the dispatch's explicit instruction, UT-J-01, UT-J-03, UT-J-04, UT-J-06, UT-J-08, and UT-J-09 were **not** re-tested and have no rows in this report — they were already re-verified this iteration via deterministic golden-script replay (evidence at `reports/qa/goal-ops-hardening-iter-45-evidence/J-01-verify.png`, `J-03-verify.png`, `J-04-verify.png`, `J-06-verify.png`, `J-08-verify.png`, `J-09-verify.png`, all present and pre-dating this agent's dispatch) and merge into the final results separately.

---

## Golden replay scripts

None written this run. Per the agent instructions, a golden replay script is written only for a journey verified **PASS**; both UT-J-05 and UT-J-07 failed, so no script was produced for either — both fall back to full live browser-qa verification next time, which is appropriate given the live, evolving nature of what was found (an active backend outage, not a stable passing state to freeze into a replay).

---

## Additional context (not a separate test, background observed during polling)

Two backfill jobs that pre-dated this agent's dispatch (`run 279`: `2026-05-02`→`2026-05-03`, started `00:23:11Z`; `run 280`: `2025-06-01`→`2026-07-17`, started `00:23:19Z` — both ranges UT-J-01/UT-J-03 expect to resolve near-instantly as "zero-work," per those journeys' own already-passing golden replay) were still shown `status: "running"` with `dates_done: 0` as of the last successful `/api/data` poll before the outage (`00:41:57Z`, ~18 minutes after they started) — i.e., signs of the same class of stall/contention were already present before this agent triggered anything. This is offered as context for whoever investigates the outage's root cause; it is not itself a UT-J-05/UT-J-07 acceptance clause and no independent verdict is rendered on it.

---

## Environment

- **Frontend URL:** http://localhost:3255 (independently healthy throughout, 200 OK at `/`)
- **Backend URL:** http://localhost:8255 (healthy at dispatch time per coordinator; entered an unresolved, complete wedge state at ~00:47-00:48Z during this run's own UT-J-05 execution and remained down through 01:21:40Z, the last probe before this report was written)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile, headless
- **Test Date:** 2026-08-04
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-45-evidence/`
