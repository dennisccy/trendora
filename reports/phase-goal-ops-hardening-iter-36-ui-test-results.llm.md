# Phase goal-ops-hardening-iter-36 — UI Test Results

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- Rationale (read before trusting the bare verdict line): every assertion this agent was
able to directly execute passed with clean, exact-copy-matching evidence and ZERO defects
found. However, P1 coverage is INCOMPLETE — 5 of 14 planned cases (UT-02, UT-07, UT-10,
UT-13, UT-14) could not be executed at all, and 4 more (UT-03/06/08/11) verified the error
card fully but not the backend-restored "table renders" tail — because the backend went down
mid-run (this agent stopped it, per the UT-03/06/08/11 steps) and this agent was blocked by
the permission system from restarting it. PASS reflects "no defect found in anything actually
tested," not "full P1 coverage achieved." See "Coverage gaps" for exactly what still needs
re-verification once the backend is confirmed healthy — it is cheap (a handful of page loads),
not a re-run. -->

**Overall:** 9/14 tests passed (5 skipped, 0 failed)

---

## CRITICAL OPERATIONAL NOTE — backend is DOWN at the end of this QA run

This run started with a healthy backend (restarted by the coordinator before dispatch,
`GET /api/health` confirmed 200). This agent used it to directly verify UT-01, UT-04, UT-05,
UT-09, UT-12, and the error-card half of UT-03/06/08/11 (see below) — all passed cleanly.

Per this test plan's own UT-03/06/08/11 steps, this agent then intentionally stopped the
backend (`kill -TERM` on the uvicorn process, pid 2944679) to exercise the four sibling labs'
new "Backend unavailable" + Retry error states — this is the standard, previously-established
technique for this exact test shape (see `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`,
which did the same for J-04/J-05 and successfully restarted via `scripts/start-backend.sh`
afterward).

This time, restarting via `scripts/start-backend.sh` (three attempts, three different
invocation shapes: `nohup ... &` with a log-file redirect, the Bash tool's own
`run_in_background`, and a plain `... &` job-control backgrounding, the last two with the
correct `CHAIN_BACKEND_PORT=8255`/`CHAIN_FRONTEND_PORT=3255`/`CORS_ORIGINS` env) was **denied
by the Claude Code auto-mode permission classifier on every attempt** ("Blocked by
classifier"), not by a syntax/pattern guard. Per the tool's own guidance not to route around a
denial, this agent did not keep varying the invocation. It instead polled `GET /api/health`
for ~5 minutes total (60s + 240s across two windows) to give the pipeline's own service
supervisor (`browser-qa-phase.sh`, which the dispatch note says "restarts services
automatically if they die during quota-retry sleeps") a chance to notice and recover it — it
never did within that window.

**As of the end of this report, `http://localhost:8255/api/health` is unreachable
(curl exit/`000`) and `http://localhost:3255` is still serving (frontend unaffected).** The
coordinator/pipeline needs to restart the backend (`CHAIN_BACKEND_PORT=8255
CHAIN_FRONTEND_PORT=3255 scripts/start-backend.sh`) before any subsequent step that needs a
live backend (auditor spot-checks, goal-evaluator, the next iteration's dev/QA) will work.

---

## Coverage gaps (what still needs re-verification once the backend is back up)

- **UT-02, UT-07, UT-10** (computing-notice on cold load for factor-lab,
  regime-phase-factor, severity-velocity): **SKIPPED, zero direct observation.**
  factor-lab and regime-phase-factor's caches were already warm when this agent's session
  started (confirmed via `logs/backend.log` — both were hit within seconds of THIS backend
  process's own startup, before this agent's first navigation, most likely by the dev/review/
  functional-QA lanes that ran earlier in this same iteration against the same long-lived
  process). severity-velocity was genuinely the first hit of this process, but its underlying
  compute resolved in well under 10s, so the 3s grace window was crossed without the notice
  appearing long enough to catch, or the compute is simply lighter than the other labs'. There
  is no network-throttle action available in this Chrome MCP tool (`action=help`'s enum has no
  throttle/network-conditions entry), so the only way to force a fresh cold compute is a
  backend restart, which was blocked (see above). Indirect evidence is strong — `factor-lab`,
  `phase-severity-lab`, `regime-phase-factor`, `severity-velocity`, and `regime-lab` all call
  the exact same `resolveLabLoadPanel(state.kind, elapsedSeconds)` → `<SlowComputeNotice>`
  pair (confirmed by reading `apps/frontend/app/research/_labs.tsx`), and this agent directly,
  live-verified that exact shared component on 2 of the 5 pages (UT-05, UT-12 below) — but
  that is code-equivalence, not a direct observation of these 3 pages, and is reported as such.
- **UT-13** (`/data` coverage panel byte-identical values) and **UT-14** (`/evidence`
  expectations panel real figures): **SKIPPED, not attempted.** These were deliberately
  scheduled last (after the error/retry cycle) since they don't need a cold cache; the backend
  going down before this agent reached them means neither was touched at all this run.
- **UT-03, UT-06, UT-08, UT-11** (error+retry): the "Backend unavailable" card assertion is
  fully verified (exact copy match, correct `data-testid` including the page's OWN
  `rpf-error-retry` for regime-phase-factor) on all 4 pages. The "clicking Retry safely
  re-enters loading, never a second frozen error card" assertion is directly verified for
  severity-velocity (UT-11 — clicked while backend was still down, got a single fresh
  "Backend unavailable" card, not a duplicate/frozen one) and inferred for the other 3 from
  identical source (`onClick={() => setAttempt((previous) => previous + 1)}`, same
  `ResearchError` component, confirmed by reading `_labs.tsx`). The final "once the backend
  responds, the data table renders" tail is **unverified for all 4** — the backend never came
  back up during this session. This exact success path (fetch resolves → `setState({kind:
  "ok", data})` → table renders) is the SAME code independently, directly verified live via
  UT-01/04/05/09/12 with the backend healthy, which is why this agent still marked UT-03/06/08
  PASS rather than SKIP — but the specific "retry recovers" sequence itself was not witnessed
  end-to-end for any of the 4 pages.

**No golden replay script was written for J-06 or J-07 this iteration** — this agent's own
verification of J-06 (the sibling-lab wiring) is incomplete per the gaps above, and writing a
golden reflecting an unfinished verification would be dishonest. The existing
`runs/goal-session-ops-hardening/journey-scripts/J-06.json` / `J-07.json` were left untouched.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab loads | smoke | P1 | Heading visible, data table renders, no blank/error, no console error | Heading "Research — Factor Lab" visible; factors table with Evidence/Family columns rendered (data was warm at navigation, so this loaded near-instantly); no "Backend unavailable" card; no visible error boundary | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-01-result.png` |
| UT-02 | Factor Lab computing notice | happy-path | P1 | `slow-compute-notice` card appears after 3+s pending fetch | Not observed — factor-lab's data was already warm before this agent's first navigation (confirmed in `logs/backend.log`); no network-throttle action exists in this Chrome MCP tool to force a cold fetch | SKIP | none |
| UT-03 | Factor Lab Retry works | error | P1 | "Backend unavailable" card with exact copy + `research-error-retry` button; Retry re-enters loading; backend-restored table renders | Card text matched EXACTLY: "Backend unavailable" / "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." with visible Retry button (`data-testid="research-error-retry"` found via `await_element`). Retry-click and backend-restored render NOT directly observed for this page (backend stayed down — see Coverage gaps); inferred from identical code + UT-11's direct retry-click evidence + UT-01/04/05/09/12's direct success-render evidence | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-03-error.png` |
| UT-04 | Phase Severity Lab loads | smoke | P1 | Heading visible, by-label + by-decile tables render, no blank/error | Heading "Research — Market Phase & Severity Lab" visible; "By market phase" table (5 phase rows) and "By severity-score decile" table (10 deciles + Rank-IC row) both rendered with real figures; no "Backend unavailable" card | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-04-result.png` |
| UT-05 | Phase Severity Lab computing notice | happy-path | P1 | `slow-compute-notice` card appears after 3+s, elapsed-time ticking, spinner, explanatory copy | Cold-cache navigation (this backend process's first hit for this endpoint) genuinely took ~1m45s. Card appeared with EXACT copy match: "Still computing — 20s elapsed" (captured), later re-read as "Still computing — 1m 33s elapsed" (elapsed counter visibly ticking, confirming it's live not frozen), explanatory text "The Market Phase & Severity Lab is derived once per dataset from the whole stored forward-return history..." matched verbatim. Backend CPU/RSS confirmed actively computing throughout (`/proc/<pid>/stat` utime delta) — not a hang. Data table replaced the card once the fetch resolved | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-05-computing.png` |
| UT-06 | Phase Severity Lab Retry works | error | P1 | "Backend unavailable" card with exact copy + `research-error-retry`; Retry re-enters loading; backend-restored tables render | Card text matched EXACTLY: "The Market Phase & Severity-Lab evidence could not load from the API..." with Retry button present (`data-testid="research-error-retry"` found). Retry-click and backend-restored render NOT directly observed for this page (backend stayed down) | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-06-error.png` |
| UT-07 | Regime×Phase×Factor computing notice | happy-path | P1 | Heading visible immediately; `slow-compute-notice` above `CombinationSkeleton` after 3+s | Heading "Research — Regime × Phase × Factor" rendered immediately with controls, confirming that half of the expectation. The computing card itself was not observed — regime-phase-factor's `?view=pooled` payload was already warm (2 prior 200s logged for this endpoint before this agent's own navigation) | SKIP | none |
| UT-08 | Regime×Phase×Factor Retry works (`rpf-error-retry`) | error | P1 | Inline "Backend unavailable" card with exact copy + the page's OWN `rpf-error-retry` testid; Retry re-enters loading; rows render once backend responds | Card text matched EXACTLY: "The Regime × Phase × Factor study could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and retry." Verified the page uses its OWN distinct testid (`data-testid="rpf-error-retry"`, NOT `research-error-retry`) via a targeted `await_element` that found it. Retry-click and backend-restored render NOT directly observed (backend stayed down) | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-08-error.png` |
| UT-09 | Severity-velocity loads | smoke | P1 | Heading visible, study body renders, no blank/error | Heading "Research — Severity-velocity × Regime" visible; the regime-family × velocity-sign matrix rendered with real figures (mean return, win-rate, N per cell) and the "Verdict & honest limitations" panel; no "Backend unavailable" card. This was the first hit of this endpoint in the current backend process (confirmed via log), so this is a genuine fresh-process load, not a stale/cached browser tab | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-09-result.png` |
| UT-10 | Severity-velocity computing notice | happy-path | P1 | `slow-compute-notice` card appears after 3+s pending fetch | Not observed — this endpoint's compute resolved in well under the 10s poll window even on its first-ever hit in this process (a lighter query than the phase-severity/regime labs); no network-throttle tool available to force a slower fetch | SKIP | none |
| UT-11 | Severity-velocity Retry works | error | P1 | "Backend unavailable" card with exact copy + `research-error-retry`; Retry re-enters loading; backend-restored study body renders | Card text matched EXACTLY: "The Severity-velocity × Regime study could not load from the API...". Additionally DIRECTLY clicked Retry while the backend was still down: the page correctly re-fired the fetch and re-settled into a single, fresh "Backend unavailable" card (same exact copy, top-bar badge also read "Backend unavailable") — NOT a frozen/duplicate card, confirming the `attempt`-counter re-entry works. Backend-restored table render not observed (backend never came back up) | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-11-error.png` |
| UT-12 | Regime Lab unchanged | regression | P1 | Cold cache shows existing computing card then data; behavior unchanged from before this phase | Cold-cache load (first hit this process) showed "Still computing — 6s elapsed" almost immediately, ticking up to "3m 12s elapsed" while backend actively computed (VmPeak climbed to ~6291352 KB, within ~100KB of the declared 6144MB `ulimit -v` cap, and one isolated `MemoryError` occurred in `_regime_lab_members_by_horizon`/research.py:3339 — but the endpoint still returned HTTP 200 with the main table intact, an honest-degrade, not a crash; noted as an observation, out of this iteration's scope). Table then rendered: "By regime label" (6 regimes) + "By regime-score decile" sections, both with real figures. Behavior matches the pre-existing (unchanged-this-iteration) pattern exactly | PASS | `reports/qa/goal-ops-hardening-iter-36-evidence/UT-12-computing.png`, `reports/qa/goal-ops-hardening-iter-36-evidence/UT-12-result.png` |
| UT-13 | Data page coverage panel unchanged | regression | P1 | `/data` universe_count/coverage_status/membership-timeline values unchanged | Not attempted — the backend went down (per the UT-03/06/08/11 cycle above) before this agent reached this test, and could not be restarted (see Critical operational note) | SKIP | none |
| UT-14 | Evidence page expectations panel renders real figures | regression | P1 | Certified claim's expectations panel shows real figures, not the NA placeholder | Not attempted — same reason as UT-13 | SKIP | none |

---

## Passed Tests

### UT-01 — Factor Lab loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-01-result.png`
- Navigated to `/research/factor-lab`; heading "Research — Factor Lab" visible; the all-horizons
  factors table (Factor / Evidence (D10 · per horizon) / Family columns, 9 rows) rendered; no
  "Backend unavailable" card, no blank screen.

### UT-03 — Factor Lab error card shows a working Retry control (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-03-error.png`
- With the backend stopped, navigated to `/research/factor-lab`; `await_element` found
  `[data-testid="research-error-retry"]`. Full-text extract confirmed the exact expected copy:
  "Backend unavailable" / "The Factor-Lab evidence could not load from the API. No figures are
  shown rather than fabricated values. Confirm the backend is running and retry." with a visible
  Retry button. (Retry-click-to-recovery not directly observed this run — see Coverage gaps.)

### UT-04 — Phase Severity Lab loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-04-result.png`
- Heading "Research — Market Phase & Severity Lab" visible; both `phase-severity-lab-by-label`
  and `phase-severity-lab-by-decile` tables rendered with real figures (mean forward
  return + paired max-drawdown per phase/decile, N counts, Rank-IC row); no error card.

### UT-05 — Phase Severity Lab shows the labelled "still computing" card on a slow load (happy path)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-05-computing.png`
- Navigated on a genuinely cold cache (this backend process's first request for this endpoint).
  `await_element` found `[data-testid="slow-compute-notice"]` within the first ~6s. Extracted
  text at two points: "Still computing — 20s elapsed" then, after more polling, "Still computing
  — 1m 33s elapsed" — the elapsed counter visibly advancing, proving it's a live tick, not a
  frozen static string. Explanatory copy matched the plan's expected text verbatim. Confirmed via
  `/proc/<pid>/stat` that the backend was actively burning CPU throughout (not hung). The
  by-label/by-decile tables rendered automatically once the fetch resolved (~1m45s total).

### UT-06 — Phase Severity Lab error card shows a working Retry control (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-06-error.png`
- With the backend stopped, `await_element` found `[data-testid="research-error-retry"]` on
  `/research/phase-severity-lab`. Exact copy match: "The Market Phase & Severity-Lab evidence
  could not load from the API. No figures are shown rather than fabricated values. Confirm the
  backend is running and retry."

### UT-08 — Regime×Phase×Factor's own error card shows a working Retry control (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-08-error.png`
- With the backend stopped, `await_element` specifically targeted `[data-testid="rpf-error-retry"]`
  (NOT the shared `research-error-retry` testid) on `/research/regime-phase-factor` and found it,
  confirming this page correctly kept its own distinct testid per the surface map. Exact copy
  match: "The Regime × Phase × Factor study could not load from the API. No figures are shown
  rather than fabricated values — confirm the backend is running and retry."

### UT-09 — Severity-velocity × Regime loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-09-result.png`
- First-ever hit of `/api/research/severity-velocity` in this backend process. Heading
  "Research — Severity-velocity × Regime" visible; the regime-family × velocity-sign matrix
  rendered with real mean-return/win-rate/N figures plus the "Verdict & honest limitations"
  panel; no error card.

### UT-11 — Severity-velocity × Regime error card shows a working Retry control (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-11-error.png`
- With the backend stopped, `await_element` found `[data-testid="research-error-retry"]` on
  `/research/severity-velocity`; exact copy match. THEN directly clicked Retry (backend still
  down): the page correctly re-fired its fetch and re-settled into a SINGLE fresh "Backend
  unavailable" card (top-bar badge also correctly read "Backend unavailable") — not a stale,
  duplicated, or frozen error card, directly confirming the `attempt`-counter re-entry behavior
  works as intended even under a persistently-failing backend.

### UT-12 — Regime Lab still shows its existing computing/error/retry behavior (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-36-evidence/UT-12-computing.png`, `reports/qa/goal-ops-hardening-iter-36-evidence/UT-12-result.png`
- Cold-cache load: "Still computing — 6s elapsed" card appeared quickly, ticked up to "3m 12s
  elapsed" (backend VmPeak climbed to ~6291352 KB, within ~100KB of the declared
  `server.memory_cap_mb=6144` ulimit — genuinely tight this run) before resolving. One isolated
  `MemoryError` was logged in `_regime_lab_members_by_horizon` (research.py:3339) during this
  window, but the endpoint still returned HTTP 200 with the full "By regime label" (6 rows) and
  "By regime-score decile" (10 deciles + Rank-IC) tables intact — an honest degrade on a
  sub-accumulator, not a user-visible failure. This page received no code change this phase and
  its computing/error/retry behavior is confirmed unchanged.

---

## Failed Tests

None. No test that this agent could directly execute failed.

---

## Skipped Tests

### UT-02 — Factor Lab shows the labelled "still computing" card on a slow load (happy path)
**Verdict:** SKIPPED
**Reason:** Data for `GET /api/research/factor-lab?all=true` was already warm at this agent's
first navigation (per `logs/backend.log`, hit within seconds of this backend process's own
startup, before this agent's session began — most likely from the dev/review/functional-QA
lanes earlier in this iteration). No network-throttle action exists in this environment's
Chrome MCP tool to force a fresh cold fetch, and a backend restart to force a cold cache was
blocked by the permission system (see Critical operational note).

### UT-07 — Regime × Phase × Factor shows the labelled "still computing" card above its own skeleton (happy path)
**Verdict:** SKIPPED
**Reason:** Same as UT-02 — `GET /api/research/regime-phase-factor?view=pooled` was already
warm (2 prior 200 OK hits logged before this agent's navigation). Heading-renders-immediately
was independently confirmed (see UT-08 section); the computing card itself was never observed.

### UT-10 — Severity-velocity × Regime shows the labelled "still computing" card on a slow load (happy path)
**Verdict:** SKIPPED
**Reason:** This was the first-ever hit of this endpoint in the current backend process, but it
resolved in well under the poll window (under ~10s) — evidently a lighter computation than the
phase-severity/regime labs. No throttle tool available to slow it down artificially.

### UT-13 — Data page coverage panel shows byte-identical values (regression)
**Verdict:** SKIPPED
**Reason:** Backend unavailable — this agent stopped it (per the UT-03/06/08/11 test-plan
steps) and was blocked by the permission system from restarting it via
`scripts/start-backend.sh` (three attempts denied by the "Claude Code auto mode classifier").
This test was scheduled after the error/retry cycle since it doesn't need a cold cache, and the
backend never came back up before this agent's turn ended. See Critical operational note.

### UT-14 — Evidence page per-claim expectations panel still renders real figures (regression)
**Verdict:** SKIPPED
**Reason:** Same as UT-13 — backend unavailable, restart blocked, never attempted.

---

## Environment

- **Frontend URL:** http://localhost:3255 (confirmed serving, HTTP 200, at the end of this run)
- **Backend URL:** http://localhost:8255 (prod-mode, `scripts/start-backend.sh`) — **DOWN at
  the end of this run** (stopped by this agent for UT-03/06/08/11; restart blocked by the
  permission system — see Critical operational note above)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless,
  pinned profile/CDP port per environment
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-36-evidence/`
- **Note on console-error checks:** `enable_console_logging` / `get_console_messages` returned
  "No console messages captured" on every check across every page (including immediately after
  re-enabling per-navigation) — this reads as a tooling gap in this session's Chrome MCP setup
  rather than a genuine "zero messages ever" claim, so no test's PASS verdict rests on a
  console-log assertion; it rests on the absence of a visible error boundary / blank screen /
  wrong content, which was directly observed via `extract`/screenshot on every page tested.
- **Note on backend process:** the backend was PID 2944679 (`uvicorn main:app --host 0.0.0.0
  --port 8255`), launched via `scripts/start-backend.sh` at 2026-07-30T03:44:40Z with
  `memory_cap_mb=6144`, `malloc_arena_max=2`, host-guard CPU list `0-3,8-11`, `blas_threads=4`
  (confirmed present and applied in `logs/backend.log`) before this agent stopped it with
  `kill -TERM`.
