# Phase goal-ops-hardening-iter-49 — UX Regression Review

**Date:** 2026-08-05

**Verdict:** UX-REGRESSION-FAIL

---

## Context note on scope

`plan.md` and the phase spec both set `Frontend Present: no`, and every artifact confirms zero files
under `apps/frontend/` were touched. Per this reviewer's own "Backend-only phase handling" rule, a
mechanical `no changes to review` PASS would normally apply here. This review does **not** take that
shortcut, for the same reason iter-9's UX review in this session didn't: `ui-impact-analyst`'s own
`user-visible-changes.md`/`ui-surface-map.md` classify this iteration as having real (if indirect)
UI impact on 8 existing surfaces, AND — decisively — the browser-qa-agent's live testing this round
(`reports/phase-goal-ops-hardening-iter-49-ui-test-results.md`, mtime 10:46, the LATEST QA-class
artifact for this iteration) found a genuine, reproducible availability regression across those exact
surfaces during a live drill. That finding is squarely this reviewer's job to surface.

---

## New Capability Discoverability

Nothing new to discover in the conventional sense — `user-visible-changes.md`, `ui-surface-map.md`, and
the dev handoff all agree: zero new pages/panels/routes/buttons/fields/labels. The "capability" this
iteration ships is a reliability promise on **already-existing** surfaces: the `/data` job-status badge
(`data-testid="job-status"`), the `/scanner-runs` table, and the `/evidence`/`/backtest`/`/research/
factor-lab` panels should now resolve to a terminal state reliably, within the already-advertised
~20-minute window, instead of silently running long or never finishing.

That promise is the actual thing to evaluate here — and the evidence is mixed-to-negative, not clean:
- **3/3 non-adversarial live drills** (backend freshly booted, no concurrent page traffic) did land inside
  budget: 1,012.71s / 1,048.22s / 1,044.77s, per `reports/perf-budgets.md` Item R Addendum 4 and the QA
  report.
- **The one live drill run under realistic concurrent usage** (an operator also browsing `/research/
  factor-lab` and `/backtest` while the backfill's finalize tail ran — exactly the kind of ordinary
  concurrent traffic nothing in the UI warns against) did **not** land inside budget. It crashed the
  entire backend outright at ~14m53s. See Regression Risk below.

No discoverability flag is warranted (nothing is hidden — there is nothing new to find), but the
underlying capability's reliability claim is not proven under realistic conditions this round.

## Regression Risk

| Shared component / surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| Entire backend process (`uvicorn`) — every page, every journey | ALL journeys (J-01 through J-09) — the process every page/API request depends on | This iteration's own `drawdown_expectations_warm` fix ran as designed under a real live drill and hit a `MemoryError` that was caught and logged gracefully (matches the existing per-item isolation convention — not itself a bug). But **immediately afterward**, a concurrent, unrelated request to `/research/factor-lab` (`research.py`'s `compute_factor_lab_all`, a function this iteration did **not** touch) threw its own uncaught `MemoryError`, which cascaded into a fatal, uncatchable `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.` The backend process died and **did not come back up for 6+ minutes** during the QA dispatch (confirmed down as late as 10:42:44 via direct polling plus a 4-minute automated recovery-check that timed out). | **Critical.** This is not a "potential" regression — it is a directly observed, reproduced-once outage of the ENTIRE product, triggered by ordinary realistic usage (browsing a second page during a routine backfill) that nothing in the UI prevents or warns against. It squarely falsifies this iteration's own target journey J-07 ("Heavy aggregates never take the service down") in a live drill. |
| `/data` readiness badge (`HealthBadge`, `data-testid="readiness-badge"`) + preflight banner | Every journey's availability signal | No code touched; behavior during the crash was itself honest (flipped to `data-state="unavailable"` / "NO-GO", did not fabricate readiness) | **Low** on its own (the badge told the truth) but it is the visible symptom of the Critical row above — for 6+ minutes, every page an operator opens shows this same "Backend unavailable" state, not just `/data`. |
| J-04 (boot/crash-recovery journey), J-08 (backtest storage-only serving), J-09 (background-compute disclosure) — all "required-still-passing" this round | Prior-phase features, explicitly named non-negotiable this round (`plan.md` Notes: "J-04 in particular has zero executed rows for 2 consecutive rounds ... is explicitly named as non-negotiable this round") | Not touched by this iteration's diff | **Confirmed regression against the phase's own Definition of Done**, not merely a risk: `ui-test-results.md`'s results table shows **UT-J-04 SKIPPED, UT-J-08 SKIPPED, UT-J-09 SKIPPED** — all three because the backend crashed before they could be attempted. J-04 now has zero executed rows for a **third consecutive round** (the plan's own binding audit-finding F3 already flagged 2 consecutive rounds as unacceptable before this one). |
| Deterministic golden-replay lane (`demo_runner.py`, `regression-replay-results.md`) | J-01, J-03, J-06, J-08, J-09 replay proof | Not touched | **Confirmed regression, separate episode:** `reports/phase-goal-ops-hardening-iter-49-regression-replay-results.md` (mtime 10:07:58, roughly one minute after the qa report and well before the browser-qa-agent's dispatch) shows **0/5 journeys executed — all 5 BLOCKED** with "backend unreachable: GET http://localhost:8255/api/health did not answer 200." This is a *second, separate* availability gap inside the same QA window (a `PRECONDITION-backend-unavailable.png` screenshot at 10:14 corroborates it), distinct from the later 10:36 crash. Across the full 10:03–10:48 QA dispatch window, the backend was down or unreachable for a meaningful fraction of the time. |

## UI vs Backend Parity

- **No hidden new capability.** `implementation-summary.md`'s "Backend-Only Items" section is honest:
  "None — there is no new user-facing control or endpoint to wire to the UI." Consistent with
  `ui-impact-analyst`'s classification and the phase's own scope (`Frontend Present: no`).
- **Minor, expected gap — not blocking.** The new per-horizon (`forward_aggregates_warm`) and per-claim
  (`drawdown_expectations_warm`) sub-phase timing breakdown — this iteration's own diagnostic
  headline — exists only in `logs/backend.log` (`"J-05 finalize-tail sub-phase timing"` lines). The
  `/data` page's existing "Stage timings" block (`data-testid="stage-timings"`) was not extended to show
  it. `user-visible-changes.md`'s own "Not Visible Yet" section discloses this honestly and it is squarely
  an internal engineering diagnostic (which horizon/claim is slowest), not an operator-facing capability
  the goal.md journeys require surfaced — so this is noted for completeness, not flagged as a discoverability
  failure.
- **A real parity gap: what was claimed vs. what was found.** `implementation-summary.md`'s "Known
  Limitations" section states, about the health-poll gap: *"It always DID recover in every test run — this
  is a disclosed rough edge, not a hang or a crash."* That statement was accurate when the developer wrote
  it (05:24), but it is **directly contradicted by evidence gathered later in the same phase**: the
  browser-qa-agent's dispatch (ending 10:46) found a real, fatal crash with 6+ minutes of non-recovery
  within the dispatch window — not a brief self-recovering blip. This isn't dishonesty (the crash post-dates
  the handoff), but it means the dev handoff and implementation-summary now understate the iteration's true
  risk profile, and neither has been revised to reflect the later finding. Downstream readers (auditor,
  evaluator) should read the QA report directly rather than trusting the implementation-summary's "never a
  hang or a crash" framing.

## Flags

### Hidden Capabilities
- None. No new user-facing capability shipped this iteration.

### Undiscoverable Capabilities
- None on the discoverability axis. (The per-horizon/per-claim log-only diagnostic is arguably an
  "undiscoverable" capability in a loose sense, but it is engineer-facing tooling explicitly scoped as
  log-only by the phase spec, not a goal.md-journey-facing capability — not flagged as a UX gap.)

### Potential Regressions
- **(Confirmed, not potential) Whole-backend crash under realistic concurrent usage.** See Regression Risk
  table, row 1. `reports/phase-goal-ops-hardening-iter-49-ui-test-results.md` lines 97–162 ("Critical
  Finding" section) has the full timeline: `drawdown_expectations_warm` (this iteration's own code) hit
  `MemoryError` and aborted gracefully at 10:36:03.525; a concurrent, untouched `compute_factor_lab_all`
  call then threw its own uncaught `MemoryError` immediately after, cascading into a fatal `OpenBLAS`
  allocation failure that killed the process; it stayed down 6+ minutes with no recovery observed during
  the dispatch. This directly contradicts J-07's Must-have promise ("Heavy aggregates never take the
  service down") in a live drill, using this iteration's own target scenario.
- **(Confirmed) J-04/J-08/J-09 produced zero executed rows this round**, the exact repeat — for J-04, a
  third consecutive time — of the plan's own binding audit-finding F3, which this iteration's spec called
  "non-negotiable." `ui-test-results.md`'s results table: UT-J-04 SKIPPED, UT-J-08 SKIPPED, UT-J-09 SKIPPED.
- **(Confirmed) TC-7(b) row completeness fails.** The phase's own DEFINITION OF DONE requires "every one of
  J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09 has at least one executed row in the merged results." J-04,
  J-05 (UT-02 FAIL — job never reached terminal status), J-08, and J-09 do not meet this bar in the current,
  latest QA artifact.
- **Audit contradiction — qa's report vs. browser-qa-agent's report.** `reports/qa/
  goal-ops-hardening-iter-49-qa.md` (mtime 10:06:56, the FIRST QA-class artifact this round) states: *"UI
  Evolution Audit: N/A — backend-only phase"* and reports only a "Basic sanity check (frontend loads, no
  crashes)" with verdict PASS. `reports/phase-goal-ops-hardening-iter-49-ui-test-results.md` (mtime
  10:46:26, the LATER, more thorough, and currently the LAST product-QA-adjacent artifact) directly
  contradicts this: **Browser QA Verdict: FAIL**, "the backend process **crashed**... It did not recover
  for the remainder of this dispatch." The qa report's "no crashes" sanity read was taken before the crash
  occurred (or before the deeper test plan ran) and has not been updated; anyone reading only `reports/qa/
  goal-ops-hardening-iter-49-qa.md` would wrongly conclude this iteration is clean on the UI/availability
  axis. TC-7(a) (browser-qa/replay pass must be the LAST product-QA-adjacent event before scoring) is
  mechanically satisfied by mtime ordering, but its intent — that the LAST verdict is the one that counts —
  points at the FAIL report, not the earlier PASS.

### Visual Consistency
- Not applicable. Zero frontend files changed (`ui-surface-map.md`: "Frontend surfaces changed: 0"). No new
  component patterns, no arbitrary styling values introduced. The readiness badge's `unavailable` state
  observed during the crash is a pre-existing, already-designed state (correctly rendered, not a new or
  inconsistent one) — the problem is that it was true and sustained, not that it looked wrong.

## Recommendation

1. **Do not close this iteration on the strength of `reports/qa/goal-ops-hardening-iter-49-qa.md` alone.**
   That report's PASS verdict and "no crashes" sanity check predate (or omit) the browser-qa-agent's later,
   fuller finding of a real, sustained backend crash. The LATEST evidence — `ui-test-results.md` (FAIL) and
   `regression-replay-results.md` (0/5, BLOCKED) — is what should drive the auditor's/evaluator's verdict.
2. **The auditor should treat J-07 as NOT passing this round.** The live drill this iteration itself ran
   under realistic concurrent usage is the exact scenario J-07 promises will never take the service down,
   and it did.
3. **J-04, J-08, J-09 need a real executed row before this iteration can close** — per the phase's own
   non-negotiable Definition of Done language, not merely "sequencing held."
4. **Recommend (not this iteration's scope, but worth logging):** `compute_factor_lab_all`
   (`research.py:1051`, `sorted(obs, ...)`) is the second, less-protected sibling of
   `_factor_decile_observations` — the function this iteration DID column-project/harden. It materializes
   an unbounded in-memory list and has no graceful memory-pressure isolation, unlike the finalize-tail warm
   loops. It is the proximate cause of the fatal crash and is a natural next target once this iteration's
   own scope closes.
5. No action required on discoverability or visual consistency — this iteration introduced no new frontend
   surfaces or styling.
