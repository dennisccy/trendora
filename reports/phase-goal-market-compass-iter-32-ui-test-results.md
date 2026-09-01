# Phase goal-market-compass-iter-32 — UI Test Results

**Phase:** goal-market-compass-iter-32
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/11 tests passed (11 skipped)

---

## Precondition Check

- `curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3255` → `000` (connection
  failed — frontend not reachable)
- `curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8255/api/health` → `000`
  (connection failed — backend not reachable either)
- Dispatch instructions explicitly stated: "Frontend is NOT available. Mark all tests as SKIPPED
  with reason: frontend not running. Do NOT attempt to run browser tests."
- Per this rule and the confirmed precondition failure, no Chrome MCP session was opened and no
  navigation was attempted. All eleven test cases from
  `reports/phase-goal-market-compass-iter-32-ui-test-plan.md` (UT-J-01 through UT-J-11, the
  regression-journey set for this backend-only iteration — the surface map confirms
  `Frontend Present: no` / zero `apps/frontend/**` diff) are recorded as SKIPPED below.
- No screenshots were captured (nothing was exercised). No golden replay scripts were written to
  `runs/goal-session-market-compass/journey-scripts/` — the replay-script instruction applies only
  to journeys verified PASS this run, and none were.
- The authoritative pass/fail record for these same journeys this iteration is the deterministic
  replay lane, `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` (per the
  test plan's own closing note) — that lane is independent of this browser-QA dispatch and is not
  affected by the frontend being down for this run.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution regression | regression | P1 | Unassigned share ≤5%; sector label identical across leaderboard, detail page, and raw API | Not executed — frontend unreachable | SKIP | none |
| UT-J-02 | What-changed regression | regression | P1 | Header names prior date + day gap; entries ordered market→breadth→sectors→themes→stocks; suppressed-count matches disclosure | Not executed — frontend unreachable | SKIP | none |
| UT-J-03 | Plain-English summary regression | regression | P1 | Summary sentences render with cited facts; retrospective stamp shown at `?asof=1996-02-01` | Not executed — frontend unreachable | SKIP | none |
| UT-J-04 | Next-session candidates regression | regression | P1 | Candidate card shows Leadership/Entry/Risk + reasons/cautions; checklist, what-would-change, and not-priority disclosures populated correctly | Not executed — frontend unreachable | SKIP | none |
| UT-J-05 | Frozen manifest stamps regression | regression | P1 | Manifest card shows mode/version/"frozen" badges and populated candidates table | Not executed — frontend unreachable | SKIP | none |
| UT-J-06 | Frozen manifest immutability regression | regression | P1 | Repeated `GET /api/compass` fetches (frontier and `as_of=2025-04-15`) byte-identical; version badge matches JSON | Not executed — frontend and backend both unreachable | SKIP | none |
| UT-J-07 | Today ten-second read regression | regression | P1 | Six body sections render in fixed order; Regime/Phase tiles populated; readiness vocabulary never inside Market state card; cross-view chart absent from `/` | Not executed — frontend unreachable | SKIP | none |
| UT-J-08 | Market page relocation regression | regression | P1 | `/market` holds full relocated surface; sidebar order Today→Market with active highlighting; `?asof=2025-04-15` shows retrospective label; returning to Latest clears `?asof` | Not executed — frontend unreachable | SKIP | none |
| UT-J-09 | Backend memory re-measurement byte-identity | regression | P1 | Addendum 43 cites evidence path + VmPeak figure vs 2.5GB target; repeated `/api/compass` and `/api/dashboard` fetches byte-identical | Not executed — backend unreachable | SKIP | none |
| UT-J-10 | Recovered trading days intact | regression | P1 | `GET /api/compass` for frontier date (2026-08-12) returns HTTP 200; manifest census unchanged from prior iteration (28 rows/18 distinct as_of/max id 28) | Not executed — backend unreachable | SKIP | none |
| UT-J-11 | Regenerated derived state serves cleanly | regression | P1 | `/` at frontier as-of loads with no error boundary/crash; What-changed/summary/next-session cards render real content; manifest version unchanged | Not executed — frontend and backend both unreachable | SKIP | none |

---

## Passed Tests

None — frontend and backend were both unreachable at dispatch time; no test was executed.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-J-01 — Sector attribution stays honest and near-complete (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running (`curl http://localhost:3255` → connection failed, HTTP code `000`)

### UT-J-02 — "What changed" still reports honest session-over-session deltas (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-03 — Plain-English summary stays deterministic and cited (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-04 — Next-session candidates still show why, why-not, and what-would-change (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-05 — Frozen next-session manifest still shows its provenance stamps (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-06 — A frozen manifest still never changes (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running; backend also unreachable (`curl http://localhost:8255/api/health`
→ connection failed, HTTP code `000`), so the `/api/compass` byte-identity spot-check could not be
performed either

### UT-J-07 — The Today page still answers the ten-second read from served values only (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-08 — The Market page still holds the full relocated surface, and history still isn't lied about (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-J-09 — Backend memory footprint re-measurement leaves no displayed value moved (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running (per dispatch instruction); backend also unreachable at
`http://localhost:8255/api/health`

### UT-J-10 — The two recovered trading days stay intact, and nothing outside them moved (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running (per dispatch instruction); backend also unreachable at
`http://localhost:8255/api/health`

### UT-J-11 — The regenerated derived state for the incident dates still serves cleanly (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running; backend also unreachable, so the `/api/compass` manifest-version
re-check could not be performed either

---

## Environment

- **Frontend URL:** http://localhost:3255 (unreachable — connection failed, curl HTTP code `000`)
- **Backend URL:** http://localhost:8255 (unreachable — connection failed, curl HTTP code `000`)
- **Browser:** Chrome via MCP (not launched — precondition check failed before any browser session
  was opened)
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-32-evidence/` (no new screenshots
  added this run; pre-existing files in this directory belong to the separate deterministic
  replay lane, not this dispatch)
