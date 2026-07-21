# Phase goal-ops-hardening-iter-7 — UI Test Results

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- All 9 UT-xx test-plan cases (incl. all 4 P1s: UT-01, UT-02, UT-06, UT-08) PASS on their own merits.
     The FAIL is driven entirely by the goal-mode regression journey J-05, which surfaced a critical,
     directly-observed backend hang (GET /api/health unresponsive for 7+ minutes) during a routine heavy
     ingest job — a hard violation of J-05's explicit acceptance ("poll GET /api/health; assert it stays
     responsive throughout"). See the J-05 section below for full evidence. -->

**Overall:** 9/11 test items passed (1 failed, 1 not-exercised/skipped)

- UT-01..UT-09 (test plan): 8 PASS, 1 SKIP (UT-05, not exercised — see below)
- Goal-mode regression journeys (in addition to test plan): J-04 PASS, **J-05 FAIL**
- J-01, J-03: not re-tested — already re-verified this run by deterministic golden-script replay per dispatch instructions; their rows are merged in separately.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Evidence page loads without errors | smoke | P1 | Heading/subtitle visible, claim list or empty-state visible, no "Backend unavailable", no console error | Page loaded with heading "Evidence", claim list visible (`evidence-claim-list` present), 7 claim rows, 7 expectations panels, no "Backend unavailable" text, no console errors | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-01-evidence-loaded.png` |
| UT-02 | First `/evidence` view after ingest is fast, Refreshed line updates | happy-path | P1 | "Refreshed:" line includes "drawdown expectations"; fresh-tab `/evidence` renders claim rows + expectations within ~3s; reload shows identical content | Ran a real backfill job (2015-06-18) via the UI form; on completion the live Job progress panel's "Refreshed:" line read "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations"; opened a brand-new tab to `/evidence` immediately after — `GET /api/evidence` resource-timing entry measured 22.4ms, all 7 claim rows + 7 expectations panels rendered instantly; reload (navigate again) produced byte-identical claim-row text | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-02-job-refreshed.png`, `UT-02-evidence-fast-first-view.png` |
| UT-03 | Persisted-run fallback card shows new Refreshed value | regression | P2 | Fresh-session "Job progress" card shows the UT-02 run with "drawdown expectations" in its Refreshed line | New tab to `/data` (no job started this tab-session) showed "Job progress" card: "backfill job · 2015-06-18 → 2015-06-18 · from a previous session", status "ok", Refreshed line included "drawdown expectations" | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-03-persisted-run-fallback.png` |
| UT-04 | Run History row shows new Refreshed value | regression | P2 | Run History row for 2015-06-18 → 2015-06-18 shows "drawdown expectations" alongside all pre-existing categories, nothing removed/reordered | Located the exact table row (`2015-06-18 → 2015-06-18`); its Refreshed text: "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations" — all pre-existing categories intact, new one appended at the end | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-04-run-history-row.png` |
| UT-05 | Unresolvable claim renders cleanly, no crash | error | P2 | Any claim row missing an expectations panel still renders all other fields; no crash | All 7/7 currently-certified claim rows had a populated `evidence-expectations-panel` — no row without one existed at test time. Per the test's own exploratory-test allowance, marked not exercised rather than forced to fail. | SKIP (not exercised) | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-01-evidence-loaded.png` (shows all 7 rows with panels) |
| UT-06 | Claim-row values byte-identical across refresh | regression | P1 | All 6 named fields + expectations table identical before/after F5 | Captured full innerText of claim row 0 (verdict, hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score, full expectations table) before and after a page reload — byte-identical strings | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-06-evidence-refresh.png` |
| UT-07 | Expectations panel is clear and self-explanatory | ux | P3 | Heading "...(N-day hold)", explanatory sentence, exact column headers, method-note + survivorship testids present with real text | Heading read "Historical drawdown & dry-spell expectations (20-day hold)"; sentence matched exactly; table headers "Phase / Max-DD depth / Underwater / Time to recover / Longest losing streak"; both `evidence-expectations-method-note` and `evidence-expectations-survivorship` present with real explanatory text | PASS | (captured via UT-01/UT-06 screenshots — same page) |
| UT-08 | Data Manager job form still renders and functions | smoke | P1 | "Start a fetch / backfill job" panel with Start/End date, Job kind dropdown (3 options), Start button | Panel present; Start-date/End-date inputs found via `aria-label="Job start date"/"Job end date"`; Job kind `<select>` had exactly 3 options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill"; Start button present (type=submit, not disabled by default) | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-08-data-manager.png` |
| UT-09 | Job form blocks incomplete date range | validation | P3 | Start button visually disabled when Start date empty; no job/run-history change | Cleared Start-date field, set End date to 2020-01-01 — Start button's `disabled` property became `true` (class list includes `disabled:cursor-not-allowed disabled:opacity-50`) | PASS | `reports/qa/goal-ops-hardening-iter-7-evidence/UT-09-start-disabled.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression (goal journey) | — | First 200 ≤5s of process start; pre-ready health carries boot phase+progress; badge matches; kill → explicit unreachable state; log ends abruptly; restart → mid-flight job shows "interrupted" | Full 6-step journey executed live (see J-04 section below) — all assertions held | PASS | `J-04-initializing-badge.png`, `J-04-backend-unavailable.png`, `J-04-interrupted-job.png` |
| UT-J-05 | J-05: Aggregates are precomputed at ingest, never on the fly | regression (goal journey) | — | Backfill an unsnapshotted day; new-state served from storage; aggregates_refreshed lists categories; cold restart reads coverage without prefill; **health stays responsive throughout a heavy ingest** | Backfill + storage-serving assertions held (see below), but the health-responsiveness assertion **failed**: `GET /api/health` became completely unresponsive (connection timeout) for 7+ minutes during/after a second back-to-back heavy ingest job, correlating with a `MemoryError` in a backend worker thread. Backend required a manual restart to recover. | **FAIL** | `J-05-backend-hung-checking.png` |

---

## Passed Tests

### UT-01 — Evidence page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-01-evidence-loaded.png`
- Navigated to `/evidence`; heading "Evidence" + subtitle visible; `data-testid="evidence-claim-list"` present with 7 `evidence-claim-row` elements, each containing a `evidence-expectations-panel`; no "Backend unavailable" text; console showed only the standard React DevTools info line, no errors.

### UT-02 — First `/evidence` view after a fresh ingest job loads fast
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-02-job-refreshed.png`, `UT-02-evidence-fast-first-view.png`
- Set Start/End date to `2015-06-18`, Job kind left at default "Backfill snapshots", clicked Start. Job completed (`status: ok`) with "1 snapshots · 1850 forward returns inserted". Its "Refreshed:" line: "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, **drawdown expectations**".
- Opened a brand-new browser tab straight to `/evidence` (first view in that tab/process-fresh sense). Used `performance.getEntriesByType('resource')` to directly measure the `/api/evidence` network call: **22.4ms** — nowhere near the ~3s budget, and nowhere near the pre-fix ~73s cold-compute this iteration targets.
- All 7 claim rows + 7 expectations panels rendered fully and immediately (verified via DOM query, not just visual). A subsequent full reload reproduced byte-identical row-0 text (including the walk-forward `n=` sample counts, which legitimately grew slightly because the new 2015-06-18 date added a data point — a correct, expected effect of the ingest, not a bug).

### UT-03 — Persisted-run fallback view shows "drawdown expectations"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-03-persisted-run-fallback.png`
- Opened a fresh browser tab (no job started that tab's session) to `/data`. "Job progress" card correctly fell back to the persisted-run view: "backfill job · 2015-06-18 → 2015-06-18 · from a previous session", status "ok", Refreshed line includes "drawdown expectations" — matches UT-02's live value exactly.

### UT-04 — Run History table row shows "drawdown expectations"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-04-run-history-row.png`
- Located the exact Run History `<tr>` containing the `2015-06-18 → 2015-06-18` cell. Its Refreshed text: "latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations" — every pre-existing category preserved in original order, new category appended last.

### UT-06 — Claim-row fields byte-identical across refresh
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-06-evidence-refresh.png`
- Captured claim-row-0's full `innerText` (verdict badge, hypothesis params, out-of-sample verdict text, control comparison, registration date, forward-walk score, and the entire expectations table with all numeric cells) before and after a full page navigation/reload — strings were identical, character for character.

### UT-07 — Expectations panel content is clear and self-explanatory
**Verdict:** PASS
- Heading: "Historical drawdown & dry-spell expectations (20-day hold)" (real integer substituted). Sentence beneath matched the spec exactly. Table headers: "Phase / Max-DD depth / Underwater / Time to recover / Longest losing streak". Both `evidence-expectations-method-note` and `evidence-expectations-survivorship` present with real, non-empty explanatory text (verified via direct `innerText` read, not just visual scan).

### UT-08 — Data Manager job form still renders and functions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-08-data-manager.png`
- "Start a fetch / backfill job" panel present with Start-date (`aria-label="Job start date"`) and End-date (`aria-label="Job end date"`) inputs, a Job-kind `<select>` with exactly 3 options ("Backfill snapshots", "Fetch EOD prices", "Fetch + backfill"), and a "Start" submit button, not disabled by default.

### UT-09 — Job form blocks incomplete date range
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/UT-09-start-disabled.png`
- Cleared Start-date, set End-date to `2020-01-01`. The Start button's `disabled` DOM property became `true`, with `disabled:cursor-not-allowed disabled:opacity-50` classes applied — matches the pre-existing guard's expected behavior.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/J-04-initializing-badge.png`, `J-04-backend-unavailable.png`, `J-04-interrupted-job.png`

Executed all 6 steps from `docs/goal.md`'s J-04 against the real running prod-mode backend/frontend:
1. Confirmed baseline `GET /api/health` → `readiness: "ready"`.
2. Started a large (6-month) backfill job to have a mid-flight job to kill.
3. Killed the backend (`kill -9`) mid-job. Restarted via `scripts/start-backend.sh` with the correct `CHAIN_BACKEND_PORT=8255`/`CORS_ORIGINS` env. Polled `/api/health` at ~150-320ms intervals from process start: **first HTTP 200 arrived at t=0.005s** (well within the 5s budget), while `readiness: "initializing"`, `warmup: {done:89,total:89,status:"running"}` — a genuine pre-ready boot-phase payload.
4. Repeated the kill+restart once more, this time loading the frontend Dashboard immediately: the top-bar badge read **"Initializing… history 89/89"** — matching the health payload's phase detail (`history 89/89`) exactly, captured live in the same window (screenshot).
5. Confirmed via a separate kill: navigating to `/data` while the backend was down showed the explicit **"Backend unavailable" / "NO-GO — do not rely on today's board."** presentation (`extract` text dump), visibly distinct from the "Initializing…" badge state (screenshot).
6. Confirmed `logs/backend.log` ends abruptly after the `kill -9` — last line was an ordinary `INFO: ... 405 Method Not Allowed` request log, no clean-shutdown entry.
7. After the final restart, the 6-month backfill job that was mid-flight when killed now showed on `/data` as **"interrupted"** (not a stuck "running" row) — confirmed via DOM read of the Job progress card (screenshot).

All J-04 acceptance clauses held: single-source readiness (badge matched health payload verbatim), correct start→200 timing, honest status transitions, and the interrupted-job recovery.

---

## Failed Tests

### UT-J-05 — J-05: Aggregates are precomputed at ingest, never on the fly
**Verdict:** FAIL
**Failure:** `GET /api/health` became completely unresponsive (connection timeout, `curl` exit 28/000) for **7+ minutes** during/after a heavy ingest job, directly violating this journey's explicit acceptance: *"While a heavy ingest job runs, poll GET /api/health; assert it stays responsive throughout."*
**Evidence:** `reports/qa/goal-ops-hardening-iter-7-evidence/J-05-backend-hung-checking.png`

**Steps taken:**
1. Confirmed `2026-05-15` (goal.md's own suggested example date) already had a snapshot (false start — not usable as "one unsnapshotted historical trading day"); queried `GET /api/runs` directly and confirmed `2010-07-15` had no snapshot.
2. Submitted a backfill job for `2010-07-15 → 2010-07-15` via the `/data` UI form (this was the SECOND heavy ingest triggered back-to-back in the same long-lived backend process this session — the first, a zero-work `2026-05-15` re-backfill whose only real work was the finalize-hook warm step, had already run ~2m26s completing cleanly with `/api/health` responsive on every poll).
3. Polled `/api/health` every ~5-6s while the job ran: **200 OK for the first ~64 seconds**, then unresponsive from that point forward.
4. Confirmed via repeated `curl -m 5` calls that health stayed at connection-timeout (`000`) for over 7 continuous minutes (05:47:01 → past 05:54:35 UTC).
5. Confirmed the backend process was alive but **fully idle** (`/proc/<pid>/stat` utime+stime delta = 0 over a 3s sample; state `S` sleeping; all 22 threads in `futex_do_wait`) — a hang, not a busy/slow computation.
6. Loaded `/data` in the browser during the hang: the badge showed **"Checking backend… / Checking board status…"** indefinitely — not the honest "Backend unavailable" state J-04 verified moments earlier — because the health request itself was hanging rather than failing fast (screenshot captured).
7. Found the root-cause signature in `logs/backend.log`: `Exception ignored in thread started by: <object repr() failed> / MemoryError:` at the exact moment health stopped responding, with no traceback (memory too exhausted even to format one). Several **earlier** `MemoryError` tracebacks (with full stack traces) were also present in the same log from `GET /api/backtest` → `forward_aggregates_cached` → a large `ScannerResult` query — unrelated to this iteration's code path, indicating the backend's `memory_cap_mb=6144` `ulimit -v` ceiling was already marginal for the current (much-grown, live) dev database before this specific ingest ran.
8. Manually killed and restarted the backend (`scripts/start-backend.sh` with correct env) to recover the environment; confirmed `/api/health`, `/api/data`, `/api/evidence` all returned fast (<100ms) afterward.
9. Confirmed the `2010-07-15` backfill job itself had **actually completed successfully** server-side before the hang set in: `status: "ok"`, "1 snapshots · 1390 forward returns", Refreshed line correctly listed all 7 categories including "drawdown expectations" — i.e., the core ingest-time-warm feature this iteration ships worked correctly; the hang was a separate, concurrent capacity failure.

**Expected:** `GET /api/health` returns 200 throughout the ingest job's lifetime (per J-05 acceptance).
**Actual:** `GET /api/health` was completely unreachable for 7+ minutes, and the frontend showed an ambiguous "Checking backend…" state rather than either a live board or an honest unreachable message during that window.

**Assessment / attribution:** The evidence points to a pre-existing capacity fragility (the `memory_cap_mb=6144` virtual-memory ceiling being marginal for the live dev DB's current size, combined with worker-thread crashes on `MemoryError` apparently leaking the shared anyio thread-pool's capacity over the session) rather than a defect newly introduced by this iteration's `drawdown_expectations` warm step specifically — the earlier unrelated `/api/backtest` `MemoryError`s in the same log predate my test and show the ceiling was already being hit by other heavy endpoints. However, this iteration's warm step adds one more memory-hungry synchronous computation to the ingest finalize hot path, making the ingest path more likely to be the trigger, and the **observed symptom is a real, reproducible violation of J-05's stated acceptance** regardless of deep-cause attribution. This is a stability/availability finding squarely within the ops-hardening goal's scope and should not be waved through as unrelated.

---

## Skipped Tests

### UT-05 — A claim with no resolvable expectations renders cleanly
**Verdict:** SKIPPED (not exercised)
**Reason:** All 7/7 currently-certified claim rows had a populated `evidence-expectations-panel` at test time — no row lacking one existed to exercise this path against. Per the test plan's own instruction ("If every claim currently has a populated panel, mark this test 'not exercised this run' rather than forcing a failure"), this is recorded as not-exercised rather than PASS or FAIL.

---

## Environment

- **Frontend URL:** http://localhost:3255 (prod-mode)
- **Backend URL:** http://localhost:8255 (prod-mode, `scripts/start-backend.sh`)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-07-21
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-7-evidence/`
- **Note:** The backend process was intentionally killed and restarted multiple times as part of executing J-04's crash-detection steps, and once more (unplanned) to recover from the J-05 hang finding. The backend was left running and healthy (`readiness: ready`, all endpoints <100ms) at the end of this QA run.
