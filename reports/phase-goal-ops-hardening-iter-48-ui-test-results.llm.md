# Phase goal-ops-hardening-iter-48 — UI Test Results

**Phase:** goal-ops-hardening-iter-48
**Date:** 2026-08-04/05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: P1 happy-path test UT-02 fails — the historical-gap-insert backfill (J-05's target scenario)
     never reaches a terminal `data_provider_runs.status` within any reasonable wait, and a hard,
     non-caveated sub-requirement ("aggregates-refreshed" line must appear within ~30s) is structurally
     unmet. Independently corroborated by the developer's own isolated live TC-1 integration test
     (`test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound`) FAILING on a clean
     throwaway backend with the identical symptom. -->

**Overall:** 4/8 tests passed (3 skipped, 1 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading, job form (start/end/kind testids), readiness badge `ready`, no console errors | All present exactly as expected; `job-kind` defaulted to "Backfill snapshots"; `readiness-badge` `data-state="ready"` | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-01-result.png` |
| UT-02 | Historical-gap backfill reaches terminal status for its fixed step | happy-path | P1 | Running+spinner immediately; `aggregates-refreshed` mentions "membership timeline" within ~30s (must NOT take minutes); terminal status typically ~5 min, honest 20-min cap | Immediate running+spinner: yes. `aggregates-refreshed` within 30s: **no — never appeared** in 31+ min; API's `aggregates_refreshed` stayed `[]` the whole time. Terminal status: **never reached** within 31+ min (exceeds the disclosed 20-min cap). Independently corroborated by the dev's own isolated live TC-1 test FAILING identically. | FAIL | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-02-fail.png` |
| UT-03 | Backfilled date renders on Scanner Runs | happy-path | P1 | `2012-06-15` row + working run-detail page | Not tested — precondition (UT-02 job terminal) never met | SKIPPED | none |
| UT-04 | Job form blocks incomplete date range | validation | P2 | Start button disabled with empty start-date | Confirmed: `disabled: true` with start="" end="2012-06-16" | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-04-result.png` |
| UT-05 | Backend stays responsive during finalize tail | error | P1 | `readiness-badge` stays `ready`; page stays navigable | `readiness-badge` = `ready` at every check across a 31+ min observation window (5+ spot checks); `/data`⇄`/scanner-runs` navigation worked throughout; `GET /api/health` returned 200 on essentially every poll (one borderline 5s-timeout in my own tight external polling loop that recovered on the very next poll — consistent with the project's own documented "contention latency, not a code regression" finding for `/api/health` under concurrent Chrome-MCP load, `reports/perf-budgets.md` line 4261) | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-05-result.png` |
| UT-06 | Evidence drawdown-expectations panel still renders correctly | regression | P2 | Populated table, real figures, no `MemoryError`/500 | `evidence-claim-regime` badge "Regime: Risk-on" found; `evidence-expectations-table` rendered 5 populated `evidence-expectations-phase-row` rows with real percentage/day figures; `evidence-expectations-unavailable` NOT present | PASS | `reports/qa/goal-ops-hardening-iter-48-evidence/UT-06-result.png` |
| UT-07 | Factor Lab decile drill-down still works | regression | P3 | Page loads, `N=` link opens samples drill-down | Page loaded ("Research — Factor Lab" heading rendered) but the first-read whole-dataset compute (`factors-table`) had not finished after 26+ min against a documented "a minute or two" norm — never reached a state where the decile grid / `N=` links existed to click | SKIPPED | none |
| UT-08 | Zero-work re-run reads honestly | ux | P2 | `no new snapshots` badge, `zero-work-note` panel, `0` new snapshots | Not tested — precondition (UT-02 job terminal) never met, and the test plan's own note bars starting a second job while one is still finishing | SKIPPED | none |

---

## Passed Tests

### UT-01 — `/data` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-48-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/data`. Heading "Data Manager" rendered. Form fields verified via
  DOM: `data-testid="job-start-date"`, `data-testid="job-end-date"` both present; `<select aria-label="Job
  kind">` defaulted to `value="backfill"` ("Backfill snapshots"). `[data-testid="readiness-badge"]` had
  `data-state="ready"` and text "Ready". No console errors surfaced (console capture in this Chrome MCP
  build returns a "not yet implemented" placeholder rather than real messages, so absence of errors here is
  a weaker signal than usual, but nothing in the page crashed or rendered an error boundary).

### UT-04 — Job form still blocks Start with an incomplete date range
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-48-evidence/UT-04-result.png`
- On a fresh `/data` tab, set `job-start-date` to `""` and `job-end-date` to `"2012-06-16"` via the
  controlled-input native setter (React-controlled inputs don't reliably accept raw `type` keystrokes when
  the field already holds a prefilled default — see Notes below). Queried the "Start" submit button's
  `.disabled` property directly: `true`. No job started, no new "Job progress" panel appeared. Pre-existing
  behavior confirmed unbroken by this iteration's diff.

### UT-05 — Backend stays responsive while a historical-gap backfill finalizes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-48-evidence/UT-05-result.png`
- Checked `[data-testid="readiness-badge"]`'s `data-state` repeatedly across the whole UT-02 wait window
  (immediately after start, and again at roughly +5, +10, +16, +20, +27, +31 minutes): **every single
  observation read `data-state="ready"`, text "Ready"** — it never flipped to `unavailable`/red at any
  point, including well past the 20-minute honest-caveat threshold where the job itself was still `running`.
  Navigated `/data` → `/scanner-runs` → `/data` mid-wait; both loads succeeded normally with no hang or
  error boundary. An independent external polling loop (`curl GET /api/health` roughly every 15-30s for the
  full duration) recorded HTTP 200 on effectively every poll; the one exception (a single `000`/timeout at
  the ~15.5-minute mark under my own tight 5s `curl --max-time`) resolved on the very next poll 2 minutes
  later, and three immediate follow-up `curl` checks all returned 200 (at 2.4s/4.2s/3.2s latency — elevated
  but not failing). This matches the project's own already-documented finding
  (`reports/perf-budgets.md` line 4261: "the sweep's 97.8-207.7ms WARN reproduces only under the concurrent
  Chrome-MCP load it disclosed... contention, not a code regression"), so it is recorded as a latency note,
  not an availability failure.

### UT-06 — Evidence page's drawdown-expectations panel renders correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-48-evidence/UT-06-result.png`
- Navigated to `/evidence`. Found `[data-testid="evidence-claim-regime"]` badge, text "Regime: Risk-on".
  Located its card's `[data-testid="evidence-expectations-table"]`: 5 rows with
  `data-testid="evidence-expectations-phase-row"`, e.g. first row "Expansion -7.42% (p90 -3.65%) n=3626 ...
  20.0d (p90 6.0d) n=2175327 (n=756)" — real populated percentage/day-count figures.
  `[data-testid="evidence-expectations-unavailable"]` was NOT present. No `MemoryError` or 500 observed for
  `/api/evidence`.

---

## Failed Tests

### UT-02 — Historical-gap backfill reaches a terminal status for its own fixed step
**Verdict:** FAIL
**Failure:** The job started for `2012-06-15` (start=end) never reached a terminal `data_provider_runs`
status in 31+ minutes of observation (well past even the test plan's own disclosed 20-minute honest cap),
AND the `aggregates-refreshed` line's explicit, non-caveated ~30-second/"must NOT take minutes"
sub-requirement never held — the line never appeared at all during the observation window.
**Evidence:** `reports/qa/goal-ops-hardening-iter-48-evidence/UT-02-fail.png`

**Steps taken:**
1. Navigated to `/data`, set `job-start-date`/`job-end-date` to `2012-06-15`/`2012-06-15`, confirmed
   "Job kind" = "Backfill snapshots" (default, unchanged), clicked "Start".
2. Immediately after: `[data-testid="job-status"]` showed "running" with the spinning `Loader2` icon —
   matches expectation. Within under a minute, "Snapshots backfilled" reached `1/1 dates` (the snapshot
   write itself is fast, consistent with the phase spec's ~12s claim).
3. Polled `[data-testid="aggregates-refreshed"]` (specifically the instance nested under the SAME
   container as the live `job-status` element, to avoid the page's other 19 instances of this testid on
   completed history rows) at repeated intervals up to 31 minutes: **it never rendered** — the live job
   panel's own text stayed at `"1 calendar day · 0 already snapshotted · 0 non-trading"` (the
   `backfill-breakdown` line) with no following `"Refreshed: ..."` line at any point.
4. Cross-checked directly against the backend API (`GET /api/data/jobs/<job_id>`) repeatedly: `status`
   stayed `"running"` and `aggregates_refreshed` stayed `[]` (empty list) for the entire 31+ minute window;
   `finished_at` stayed `null`; `current_activity` stayed frozen at `"scanning 2012-06-15 (1/1)"` the whole
   time (never updated to reflect any finalize-tail phase).
5. Read `logs/backend.log`'s new iter-48 phase-timing instrumentation for this exact job
   (`job=0ce8e2fb0bd94e52ac3c191080ace831`): `coverage_membership_timeline_refresh` completed in **21.01s**
   and `per_date_coverage_warm`/`market_phase_warm` completed shortly after (7.05s / 28.02s) — i.e. the
   SPECIFIC step this iteration claims to fix (the membership-timeline finalize step) genuinely IS fast when
   it runs. But no further phase-timing lines were EVER logged for this job afterward (no
   `forward_aggregates_warm`, `research_hot_keys_warm`, `drawdown_expectations_warm` entries appeared in
   31+ minutes), meaning the finalize tail stalled somewhere after `market_phase_warm` and never returned.
6. Read `apps/frontend/app/data/page.tsx`'s `BackfillBreakdown` component: the `"Refreshed: ..."` line only
   renders when `aggregatesRefreshed.length > 0`. Read
   `apps/backend/app/engine/data_manager.py`: `prog.aggregates_refreshed` is assigned exactly ONCE (line
   4928), as the return value of `_refresh_ingest_aggregates(...)` — i.e. only after the ENTIRE finalize
   tail (all phases, including the still-unbounded `drawdown_expectations_warm`) either completes or is
   caught by isolation and control returns. There is no incremental/live exposure. This makes the "must NOT
   take minutes" sub-requirement structurally unmeetable by the current implementation whenever ANY later
   phase (in three unrelated prior job log samples, `forward_aggregates_warm` alone consistently took
   100-153s) runs long — independent of the historical-gap fix's own speed.
7. Found strong independent corroboration in this session's shared scratchpad
   (`.cache/iad/shared/.../scratchpad/tc1_live.log`, written ~21:44 UTC, roughly an hour before I started my
   own drill): the developer's own new live integration test,
   `test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound` (TC-1/TC-2/TC-3/TC-4),
   run against a clean, dedicated **throwaway backend with no contention from my session**, **FAILED**:
   `AssertionError: job fd064cfc70b44b82a6fa27acdc665634 did not reach terminal status within 1200.0s` — the
   job (a different historical-gap date, `2005-05-24`) showed the IDENTICAL symptom: `aggregates_refreshed:
   []`, `current_activity: 'scanning 2005-05-24 (1/1)'` frozen, never terminal, for the full 20-minute bound.
   `1 failed, 11 deselected in 1212.49s`, `EXIT_CODE=1`. This rules out "my QA session's own concurrent load
   caused this" as the sole explanation — the identical hang reproduces on an isolated backend.

**Expected:** Job reaches a terminal status within the measured bound; `aggregates-refreshed` mentions
"membership timeline" within ~30 seconds.
**Actual:** Job never reached terminal in 31+ minutes (my run) / failed the developer's own 20-minute bound
test (isolated run); `aggregates-refreshed` never appeared during that window at all.

**Note (not counted toward the FAIL, included for completeness):** The specific `coverage_membership_
timeline_refresh` phase itself DOES complete quickly (21.01s, matching the phase spec's ~10-25s claim) —
the diagnosis/instrumentation part of this iteration's work is sound. The failure is that the finalize tail
as a WHOLE still does not reach a terminal outcome, so the user-visible acceptance (a terminal job status,
`aggregates-refreshed` evidence) is not delivered — this is exactly J-05's Definition-of-Done requirement,
now failing a 5th consecutive round.

---

## Skipped Tests

### UT-03 — Backfilled historical date renders its stored snapshot on Scanner Runs
**Verdict:** SKIPPED
**Reason:** Precondition ("UT-02's job has reached a terminal status") was never met — see UT-02. Did not
navigate to `/scanner-runs` to check for a `2012-06-15` row's terminal-state rendering, since the
underlying job was still `running` throughout the entire QA session.

### UT-07 — Factor Lab still loads and its existing decile drill-down link still works
**Verdict:** SKIPPED
**Reason:** The page itself loaded correctly (`Research — Factor Lab` heading rendered, no error card), but
the Factor Lab's documented first-read whole-dataset derivation ("can take a minute or two on a deep
history") had not completed after 26+ minutes of observation, so no `factors-table` / decile grid /
`N=` sample-link ever existed to click. Backend log shows a directly relevant contention signal:
`WARNING trendora.research: factor_lab_all single-flight wait elapsed or owner failed for
key=('all', 'r2906-f6491695-allh-mdd-v1', 20) after 900s — computing independently (duplicate compute
possible)` — i.e. this request was itself waiting on ANOTHER concurrent computation of the same cache key
for 900s before giving up and recomputing from scratch. Unlike UT-02, I did NOT find independent isolated
evidence that this specific behavior is a regression — the shared scratchpad's `tc6_full.log` (the
developer's own 5-consecutive-run memory-pressure drill for `samples.py`'s `total`/`regime` bound, the code
path this endpoint exercises) shows **8 passed, 0 failed, no MemoryError**, `EXIT_CODE=0`. This SKIP
reflects severe contention during this specific QA session (my own concurrent `/data` job + factor-lab
request + apparently other concurrent backend activity on the same shared process), not a confirmed product
defect.

### UT-08 — A zero-work re-run reads honestly, never as a fabricated success
**Verdict:** SKIPPED
**Reason:** Precondition ("UT-02's backfill for 2012-06-15 has already completed with `snapshots_created >=
1`" at a TERMINAL status) was never met — see UT-02. Also, the test plan's own operating note explicitly
bars starting a second job while one is still finishing, which ruled out attempting this test regardless.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health confirmed 200 throughout)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned
  profile
- **Test Date:** 2026-08-04 22:44 UTC – 2026-08-04 23:22 UTC (~40 minutes; UT-02's own backfill job ran
  22:50:27 UTC → still `running` at last check 23:21:39 UTC, 31+ minutes)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-48-evidence/`
- **Note on environment contention:** this session ran concurrently with what other in-session evidence
  (task-list state and the shared scratchpad's `tc1_live.log`/`tc6_full.log`/`tc6_quick.log`) indicates was
  the developer's own TC-1/TC-6 test runs on the SAME shared backend/host, which measurably slowed several
  operations (elevated `/api/health` latency, an 900s single-flight cache-wait timeout on the Factor Lab
  request). Where I could independently corroborate a finding against isolated/non-contended evidence (the
  developer's own throwaway-backend `tc1_live.log` for UT-02, and `tc6_full.log` for UT-06/UT-07's
  underlying code path), I did so explicitly above and weighted verdicts accordingly — UT-02's FAIL is
  evidenced independently of contention; UT-07's SKIP is attributed to contention, not a confirmed defect.

## Golden Replay Scripts

No new golden replay script was written this run. UT-02/UT-03/UT-08 (the J-05 journey) did not reach a
verifiable PASS state, so no script was recorded for it per the "only write a script for a journey you
verify PASS" rule. UT-07 (part of J-07's regression surface) also did not reach a verifiable state. J-04 was
not covered by the test plan this iteration (no explicit UT case named it) and J-05/J-07 are the only two
target journeys in scope for this dispatch; no other new goldens apply.
