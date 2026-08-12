# Phase goal-ops-hardening-iter-70 — UI Test Results

**Phase:** goal-ops-hardening-iter-70
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->
<!-- This run: backend unreachable throughout the QA window (see Skipped Tests / Environment below).
     Per browser-qa-agent Rules ("Never debug or restart the app — that is a SKIPPED with reason, per the
     skill rules"), the agent did not attempt to start/restart the backend itself. -->

**Overall:** 0/8 tests passed (8 skipped)

---

## Precondition check

- Frontend: `http://localhost:3255` responded HTTP 200 (production build, freshly started 15:14:12 BST /
  `next start -p 3255`, PID 1910751) — reachable throughout.
- Chrome MCP: available and used (`mcp__plugin_superpowers-chrome_chrome__use_browser`); a live navigation
  to `http://localhost:3255/` succeeded and rendered the app shell.
- **Backend: `http://localhost:8255/api/health` was unreachable (connection refused, HTTP status `0`) for
  the entire QA window.** Evidence:
  - `logs/backend.log` shows `start-backend.sh: launching at 2026-08-12T14:14:12Z` (= 15:14:12 BST),
    `Started server process [1909563]`, normal operation (health polls, warmup cache fills logged through
    `2026-08-12 15:15:00,301`), then a clean shutdown sequence — `Shutting down` / `Waiting for application
    shutdown.` / `Application shutdown complete.` / `Finished server process [1909563]` — with the log
    file's last write at `15:21` BST (file mtime). No subsequent `Started server process` line appears
    anywhere after that.
  - `ps aux` showed no `uvicorn`/backend process listening on 8255 at any point this run.
  - Three separate polling windows, all `http_status=0`:
    1. Canonical `scripts/qa/poll_health.py`, 36 polls, 15:26:09–15:26:44 BST — 0/36 answered.
    2. Manual curl loop, 15s cadence, 15:28:13–15:30:59 BST — 0/12 answered.
    3. Canonical `scripts/qa/poll_health.py`, 300 polls (~5 min), 15:32:24–15:37:24 BST — 0/300 answered.
    4. Final spot check at 15:37:43 BST — still `000`.
  - Total confirmed-down span: from the 15:21 BST shutdown through the final 15:37:43 BST check — **≥16
    minutes** with zero successful responses across ~350+ individual polls, and no backend process ever
    observed running during that span.
  - A live browser navigation to `http://localhost:3255/` during this window rendered the frontend's own
    honest degraded state: readiness badge/preflight banner text **"Backend unavailable" / "NO-GO — do not
    rely on today's board." / "Backend is unavailable — the preflight check could not run."**, and the
    Dashboard card **"Backend unavailable — The dashboard could not load the market regime from the API.
    Nothing is fabricated — confirm the backend is running and reload."** Screenshot:
    `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png`.

This is a QA-harness infrastructure precondition failure (the backend service this iteration's own
dispatch note says `browser-qa-phase.sh` manages did not stay up / was not restarted before or during this
dispatch), not a product defect discovered by testing. Per the browser-qa-agent's Rules ("Never debug or
restart the app — that is a SKIPPED with reason, per the skill rules" and "Never re-run a test that already
passed this invocation" / budget rules generally), this agent did not attempt to run `scripts/start-backend.sh`
or otherwise revive the backend itself, and did not proceed to drive the UI test plan or the goal-mode
regression journeys against a backend that cannot serve real data. All 8 planned test cases (the full test
plan — every case in it is a regression case per the backend-only-iteration convention) are recorded
SKIPPED below with this shared reason.

No golden replay script was written for any journey this run (none passed) — the existing goldens in
`runs/goal-session-ops-hardening/journey-scripts/J-{01,03,04,05,06,07,08,09}.json` are left untouched.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | Both backfills accepted, exact counts, persisted run history, populated `/scanner-runs/748` | Not exercised — backend unreachable | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-03 | No per-run range cap (>370 days accepted) | regression | P1 | 412-day span accepted, chunked execution, exact counts | Not exercised — backend unreachable | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Readiness badge reaches `data-state="ready"` ≤20s, preflight banner visible, `last-run-status` non-blank | Frontend renders "Backend unavailable" / "NO-GO" — backend never reachable | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | regression | P1 | Live one-day backfill completes, aggregates refresh, `/scanner-runs` populated | Not exercised — backend unreachable (job could not even be submitted) | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-06 | Pages load only what they need (budget sweep) | regression | P1 | All 11 routes render real content within stated budgets | Not exercised — backend unreachable (pages would render error/empty states, not a meaningful budget measurement) | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-07 | Heavy aggregates never take the service down (target) | regression | P1 | Readiness badge `ready`, backtest/data panels render real background-compute state from `GET /api/health` | Not exercised — backend unreachable, so `GET /api/health` itself (this iteration's own changed endpoint) could not be observed | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-08 | Backtest evidence serves from storage only | regression | P1 | `/backtest` shows stored evidence-aggregate/evidence-summary panels | Not exercised — backend unreachable | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| UT-J-09 | Backend discloses its own background-compute activity | regression | P1 | "Previous available date" returns immediately, `/data` background-compute panel discloses scope | Not exercised — backend unreachable | SKIP | `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |

---

## Passed Tests

None this run.

---

## Failed Tests

None this run — no test was driven far enough against a live backend to produce a genuine pass/fail
signal; recording any of these as FAIL would misattribute an infra outage to a product defect.

---

## Skipped Tests

### UT-J-01 — Backfill honors requested range, explains zero-work
**Verdict:** SKIPPED
**Reason:** Backend unreachable — `GET http://localhost:8255/api/health` connection-refused throughout the
QA window; the `/data` job form's Start/End date submission depends on the backend and could not be
exercised. See "Precondition check" above for full evidence.

### UT-J-03 — No per-run range cap (>370 days accepted)
**Verdict:** SKIPPED
**Reason:** Backend unreachable — same as UT-J-01; the backfill submission this test requires cannot reach
a live job engine.

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** SKIPPED
**Reason:** Backend unreachable — the readiness badge and preflight banner render an honest
"Backend unavailable" / "NO-GO" state (confirmed by live navigation, screenshot attached) rather than the
`data-state="ready"` this test requires; `/data`'s `last-run-status` cannot render a persisted value with no
backend to serve it.

### UT-J-05 — Aggregates precomputed at ingest, never on the fly
**Verdict:** SKIPPED
**Reason:** Backend unreachable — this is a real live-ingest journey (job submission through
`POST` to the backend); with no backend process running, the job cannot even be accepted, let alone run to
completion.

### UT-J-06 — Pages load only what they need (budget sweep)
**Verdict:** SKIPPED
**Reason:** Backend unreachable — every budget-gated endpoint this test measures (health/readiness, AAPL
bars, `/data` availability, `/api/runs`) depends on the backend; with it down, every page would show the
same degraded "Backend unavailable" state rather than real content, which would not be a meaningful budget
measurement.

### UT-J-07 — Heavy aggregates never take the service down (target)
**Verdict:** SKIPPED
**Reason:** Backend unreachable — this test specifically observes `GET /api/health`'s served fields (the
exact endpoint this iteration changed to read from a background-refreshed cache); with the backend down,
`GET /api/health` cannot be observed at all, so this test cannot even indirectly exercise this iteration's
own change.

### UT-J-08 — Backtest evidence serves from storage only
**Verdict:** SKIPPED
**Reason:** Backend unreachable — `/backtest`'s evidence-aggregate/evidence-summary panels have no data to
render without the backend.

### UT-J-09 — Backend discloses its own background-compute activity
**Verdict:** SKIPPED
**Reason:** Backend unreachable — the "Previous available date" action and the `/data` background-compute
panel both depend on live backend state.

---

## Environment

- **Frontend URL:** http://localhost:3255 (reachable, HTTP 200, production build started 15:14:12 BST)
- **Backend URL:** http://localhost:8255/api/health (unreachable — connection refused for the entire QA
  window; last observed clean shutdown of PID 1909563 at ~15:21 BST per `logs/backend.log`, no restart
  observed through the final check at 15:37:43 BST)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile —
  headless, not switched
- **Test Date:** 2026-08-12
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-70-evidence/`
  (`INFRA-backend-down.png` — shared evidence of the "Backend unavailable" degraded state observed on `/`)
