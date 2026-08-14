# Phase goal-ops-hardening-iter-79 — UI Test Results (LLM lane)

**Phase:** goal-ops-hardening-iter-79
**Date:** 2026-08-14
**Written by:** browser-qa-agent (LLM lane — Chrome MCP, independent of the deterministic replay lane)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 tests passed (0 skipped, 0 failed) — with disclosed partial-coverage notes on J-04 and J-08 below.

---

## Context and how this lane relates to the replay lane

This is an `evidence`-depth closeout-confirmation round; no product code changed (backend/frontend diff
is empty this iteration). The dispatch instructed testing J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09,
while also noting a deterministic replay lane verifies the same set separately. I confirmed that lane
already ran before/during this session: `reports/phase-goal-ops-hardening-iter-79-regression-replay-results.md`
(written by `demo_runner.py`) records 8/8 PASS with its own evidence screenshots
(`reports/qa/goal-ops-hardening-iter-79-evidence/J-0X-verify.png`, timestamped 23:57–00:38 today). I did not
overwrite those files. Per this iteration's explicit "binding carries" note, I did not regenerate any of the
existing golden replay scripts in `runs/goal-session-ops-hardening/journey-scripts/` (all 8 already exist,
dated Aug 12–13, and J-05..J-09's are called out as byte-frozen) — I left `journey-scripts/` untouched.

This report is the independent LLM lane: I drove the real running app (backend :8255, frontend :3255, both
confirmed HTTP 200 at start and end of this session) via Chrome MCP myself, cross-checked against the live
`GET /api/health` and `GET /api/data` payloads, and captured my own fresh evidence (files suffixed `-llm` in
the evidence directory), rather than only reading the replay lane's output.

**Tooling note (not a product defect):** on `/data`, which renders a very large availability-heatmap grid
(DOM interactive-element count observed at 5,475+), the Chrome MCP `screenshot` action reliably returned a
solid-color blank image for ANY scroll position other than the very top of the page — even immediately after
`restart_chrome` — while `getBoundingClientRect()`/computed-style inspection of the same DOM elements at the
same moment confirmed they were real, correctly positioned, correctly styled, and visible (non-zero size,
distinct background color from the page). I treat this as a screenshot-capture artifact of the automation
tool on this heavy page, not a blank/frozen UI state, and verified the affected acceptance points via DOM
text extraction (`extract`/`eval`) instead, which worked correctly throughout. This is disclosed rather than
silently worked around.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | happy-path | P1 | May backfill reports dates_total=19; weekend-only reports 0 trading/2 non-trading; re-run is zero-work 19 already-snapshotted+9 non-trading; all persist across reload; zero-work visually distinct from success | Triggered all 3 jobs live via the `/data` form (run ids 522/523/524). 522: dates_total=19, already_snapshotted=19, non_trading=9, calendar_days=28. 523 (weekend-only 05-02→05-03): dates_total=0, non_trading=2, calendar_days=2. 524 (re-run): 0 created, 19 already-snapshotted, 9 non-trading, 28 calendar days. Reload confirmed all 3 rows persisted in Run history with identical figures. `/scanner-runs` lists 2026-05-04, 2026-05-15, 2026-05-29; opened 2026-05-15 (id 739) — immutable snapshot renders stored Market Regime 67.83, "Scanned 2026-07-20 17:31:10." DOM inspection of the Run-history table: zero-work rows carry `data-testid="run-status"` class `border-border bg-surface-2 text-text-muted` text "no new snapshots"; a genuine productive row (2005-08-16, 1 snapshot created) carries `border-pos bg-surface-2 text-pos` text "ok" — visually distinct, confirmed in the raw HTML, not just inferred | PASS | `reports/qa/goal-ops-hardening-iter-79-evidence/J-01-llm-scanner-run-2026-05-15.png` |
| UT-J-03 | No per-run range cap | happy-path | P1 | A >370-day span (2025-06-01→2026-07-17, 412 calendar days) is accepted, no "range too large" rejection, executes | Triggered live via the form (run id 525): accepted with HTTP 200/`status:"ok"`, dates_total=283, calendar_days=412 (>370), no error/rejection of any kind. Confirmed via Run-history table after reload showing the same row persisted | PASS | `reports/qa/goal-ops-hardening-iter-79-evidence/J-03-llm-data-top.png` |
| UT-J-04 | Non-blocking boot with visible status | happy-path | P1 | Boot→first-200 ≤5s; pre-ready payload carries phase/progress; crash→explicit unreachable state; logfile has boot events, truncates on crash; interrupted job shows explicit state | **Partial this round by design:** steps 1/2/3/4/6 all require restarting or killing the live backend process, which my operating constraints for this session explicitly forbid ("you may not restart the app yourself"), and the iteration's binding note carries steps 3/5/6 forward from the 2026-07-31 and prior-round drills while `apps/backend/app/` stays out of the diff. What I verified fresh and live: `GET /api/health` returns HTTP 200 with `readiness:"ready"`, a structured `warmup:{done:89,total:89,status:"ok"}` phase field, and `preflight.verdict:"GO"`; the top-bar badge on every page visited showed "Ready" (never a bare/ambiguous state); `logs/backend.log` exists, is being actively written (30MB, includes `Application startup complete.` / `Uvicorn running on...` boot lines plus live request/job log lines matching my own triggered jobs' timestamps) — confirming the persistent logfile mechanism is live and working. The restart/crash/interrupted-job-specific assertions were not independently re-driven this round; they rest on the carried 2026-07-31 evidence plus this round's replay-lane PASS (`J-04-verify.png`) | PASS (with disclosed partial coverage — see above) | `reports/qa/goal-ops-hardening-iter-79-evidence/J-04-llm-ready-badge.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | happy-path | P1 | Ingest-time aggregates serve from storage with no request-time recompute; cold `/data` renders coverage from a persisted payload without a whole-table prefill; health stays responsive during heavy ingest | Every backfill I triggered (522/523/524/525) returned an explicit `aggregates_refreshed` list (forward_aggregates, research_hot_keys, factor_lab_all, drawdown_expectations) in its persisted run record — computed once at ingest, not on read. `/data`'s Dataset Coverage panel read "Coverage as of a prior scan (version r2999-rc2999-b2026-08-03-bc3306390-h200) — refreshes on the next data job," i.e. explicitly a persisted, versioned payload, not a live recompute. `/api/data` and `/api/stocks/AAPL/bars` both answered in well under a second repeatedly. During this round's cascade of background aggregate warms (5 separate windows, see J-07), I ran a canonical `scripts/qa/poll_health.py` drill (304 polls at 1 Hz) and every single poll answered HTTP 200. **Not independently re-verified this round:** step 3's specific "restart cold + no 3.3M-row prefill" claim requires a backend restart, which I could not perform (see J-04); this rests on carried/replay-lane evidence | PASS (restart-cold sub-claim not re-driven — see note) | `reports/qa/goal-ops-hardening-iter-79-evidence/J-05-llm-coverage-persisted.png` |
| UT-J-06 | Pages load only what they need | happy-path | P1 | Nav pages load within budget, no frozen/blank frames, no unbounded scans | Visited `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/scanner-runs/739`, `/backtest`, `/watchlist`, `/research`, `/research` Factor Lab — every page rendered fully styled with real data, no errors in the captured console logs. Timed the primary on-load API endpoints directly: `/api/health` 0.045s, `/api/data` 0.21s, `/api/stocks` 0.23s, `/api/stocks/AAPL/bars` 0.36s, `/api/sectors` 0.017s, `/api/themes` 0.024s, `/api/evidence` 0.13s, `/api/watchlist` 0.032s, `/api/runs` 0.48s, `/api/backtest` 0.12s — all comfortably inside the committed budgets in `reports/perf-budgets.md`. See the tooling note above re: `/data` below-the-fold screenshots specifically (DOM-verified, not a real blank frame) | PASS | `reports/qa/goal-ops-hardening-iter-79-evidence/J-06-llm-sectors.png` |
| UT-J-07 | Heavy aggregates never take the service down | happy-path | P1 | `GET /api/health` answers 200 throughout a heavy background aggregate warm, within budget; no deadlock/wedge | My own exploratory `/api/backtest?as_of=...` requests against several never-warmed historical dates organically triggered a chain of 5 separate background-compute warm windows this session (2026-07-31 re-warm 499.5s / 173.5s, 2010-03-15 6.9s, 2012-01-10 30.3s, 2015-06-20 53.2s, 2018-09-05 31.4s, 2003-04-01 1.9s — several overlapping/queued, a materially heavier concurrent load than the spec's single-warm scenario). I ran the canonical `scripts/qa/poll_health.py` (1 Hz) spanning this whole cascade: **304/304 polls returned HTTP 200, 0 breaches of the 2s bounded-window ceiling, max observed latency 0.55s.** The process never wedged, never 500'd, and continued serving already-warmed dates near-instantly throughout (e.g. 0.036–0.11s for `/api/backtest` on already-complete as-of values while another warm was active). Per the binding note, steps 3-4 (VmPeak margin, induced-pressure abort) were not redone this round — they stand on the 2026-07-31 drill and iter-73/74's `reports/perf-budgets.md` Addenda 38/39 (42.3% margin, zero non-200s), consistent with "no code changed" | PASS | `reports/qa/goal-ops-hardening-iter-79-evidence/J-07-poll-health.csv`, `reports/qa/goal-ops-hardening-iter-79-evidence/J-07-llm-badge-during-bcw.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | happy-path | P1 | `/backtest` serves last-good stored evidence instantly with a refreshing indicator during a version bump; never blocks on compute | Requesting `/api/backtest?as_of=2010-03-15` (a date with no cached evidence for the then-current dataset version) returned immediately with `evidence_status:"refreshing"`, `evidence_asof:"2005-07-15"` (a real prior stored version, not a blank/frozen response) while `GET /api/health` simultaneously showed the same as-of dispatched into `background_compute.active`. `/backtest` (latest) and already-warmed as-of dates consistently answered in 0.03–0.12s. **Disclosed observation, not treated as a regression:** when I fired several DIFFERENT never-warmed as-of requests in quick succession (deliberately stress-testing beyond the spec's single-warm scenario), one request (`as_of=2003-04-01`, issued while a different as-of's warm was already in flight) took 9.3s to respond — over the ≤1.5s budget. `docs/goal.md`'s J-09 acceptance explicitly scopes "bounding concurrency" as out-of-scope/owner-deferred (backlog card B-1107), so I attribute this to that already-acknowledged gap rather than a newly-discovered defect, and it only appeared under concurrent-request pressure I manufactured, not the journey's own single-warm steps. All single-request, non-concurrent measurements stayed well within budget | PASS (concurrency-stress observation disclosed above, tied to acknowledged B-1107 scope, not scored as a new failure) | `reports/qa/goal-ops-hardening-iter-79-evidence/J-08-llm-backtest-latest.png` |
| UT-J-09 | The backend discloses its own background-compute activity | happy-path | P1 | Badge shows "Ready" + explicit background-compute detail during a window; `/data` panel shows the same field with as-of/elapsed/horizons; idle state + last-outcome after completion; scope disclosed as process-lifetime | Caught a genuine in-flight background-compute window live (not self-triggered) on first navigation: dashboard badge showed **both** "Ready" and a pulsing "background compute running (1)" chip (`data-testid="background-compute-indicator"`) simultaneously — never a bare Ready. The `/data` page's Background compute panel, read via DOM text extraction, showed "as-of 2026-07-31 · elapsed 4m 37s · horizons 2/5 · dataset r2999-f6609955" and "Since the last backend restart — this history is process-lifetime only, never persisted." — matching the acceptance's honesty-about-scope requirement verbatim. After the window completed, re-polled: badge returned to plain "Ready" (chip gone) and `GET /api/health`'s `background_compute.active` was `[]` with `recent_outcomes` carrying the completed window's real measured `duration_ms:499545`. Repeated for 4 more self-triggered windows later in the session, all showing the same honest active→idle/last-outcome transition with real durations, never a fabricated percentage or ETA | PASS | `reports/qa/goal-ops-hardening-iter-79-evidence/J-09-inflight-badge.png`, `reports/qa/goal-ops-hardening-iter-79-evidence/J-09-result.png` |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-01-llm-scanner-run-2026-05-15.png`
- Live-triggered all 3 required jobs through the actual `/data` form (not just read from history); confirmed the `data_provider_runs` partition contract holds (`dates_total` = non_trading + already_snapshotted + snapshots_created, calendar_days = dates_total + non_trading) for both the productive-range and weekend-only shapes.
- Confirmed in raw DOM/CSS that zero-work rows are visually distinct from a genuine "ok" success row (different badge classes/colors), not merely different text.

### UT-J-03 — No per-run range cap
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-03-llm-data-top.png`
- Live-triggered a 412-calendar-day backfill request (>370) through the UI form; accepted with no rejection, executed to completion (283 dates), persisted to Run history across reload.

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** PASS (partial coverage disclosed)
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-04-llm-ready-badge.png`
- Confirmed live, current-state readiness (health 200, structured phase payload, Ready badge, active persistent logfile). Restart/crash/interrupted-job-specific steps rest on carried evidence + this round's replay-lane PASS, not re-driven live (see Results Table for why).

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS (one sub-claim not re-driven)
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-05-llm-coverage-persisted.png`
- Every live-triggered ingest job returned an explicit persisted `aggregates_refreshed` list; `/data` coverage panel explicitly labeled as a versioned prior-scan payload; health stayed responsive across a 304-poll canonical drill spanning 5 real background aggregate warms.

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-06-llm-sectors.png`
- All 13 nav surfaces visited rendered correctly with real data; all timed on-load API calls well inside `reports/perf-budgets.md` budgets.

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-07-poll-health.csv`
- Canonical `scripts/qa/poll_health.py` drill: 304/304 polls HTTP 200, 0 breaches of the 2s bounded-window ceiling, across a heavier-than-spec cascade of 5 concurrent/queued background aggregate warms I organically triggered.

### UT-J-08 — Backtest evidence serves from storage only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-08-llm-backtest-latest.png`
- Confirmed instant last-good serving + refreshing disclosure on a fresh never-warmed as-of; confirmed byte-fast responses for warmed dates. One concurrency-stress latency observation disclosed and attributed to the acknowledged B-1107 scope gap, not scored as a defect.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-79-evidence/J-09-inflight-badge.png`
- Caught and verified a genuine in-flight disclosure window (badge + `/data` panel, both simultaneously honest) and its transition to an honest idle/last-outcome state with a real measured duration, unprompted by my own actions on the first instance.

---

## Failed Tests

None.

---

## Skipped Tests

None. Both services were confirmed HTTP 200 at the start and the end of this session; Chrome MCP was
available throughout (one `restart_chrome` was needed mid-session after a screenshot-rendering issue,
which briefly and unintentionally flipped to headed mode — immediately corrected back to headless via
`hide_browser` per this session's operating rules, and the pinned profile/port were never changed).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless throughout except one brief unintended flip immediately corrected
- **Test Date:** 2026-08-14
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-79-evidence/` (files suffixed `-llm` are this lane's own; `-verify.png` files belong to the separately-run deterministic replay lane, `reports/phase-goal-ops-hardening-iter-79-regression-replay-results.md`)
- **Golden replay scripts:** left untouched in `runs/goal-session-ops-hardening/journey-scripts/` — all 8 already existed (dated Aug 12–13) and the iteration's binding note directs not regenerating J-05..J-09's; I did not regenerate J-01/J-03/J-04's either, since this was a verify-only round with no product diff and the existing goldens were already reconfirmed fresh by today's replay-lane pass.
