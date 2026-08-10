# Phase goal-ops-hardening-iter-55 — UI Test Results

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 tests passed (0 skipped)

---

## Environment note (infrastructure recovery)

An earlier pass of this dispatch recorded a SKIPPED verdict because
`http://localhost:8255/api/health` was unreachable (connection refused) for ~12 minutes of active
polling, with an empty backend startup log. The coordinator restarted the backend from the pump side
and confirmed it live (`curl` → `200`). I independently re-confirmed before touching anything
(`curl http://localhost:8255/api/health` → `200`, `curl http://localhost:3255` → `200`) and re-confirmed
again at the very end of this run — both services were healthy for the entire duration of the pass below.
The full 7-case test plan was then executed for real against a live backend, superseding the earlier
SKIPPED result. The one screenshot from the outage (`ALL-backend-down.png`) is left in the evidence
directory as a historical record of the earlier state; it is not evidence for any test below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors (smoke) | smoke | P1 | Page renders, "Start a fetch / backfill job" panel visible, readiness pill `data-state="ready"`, no console errors | Page rendered fully (82 buttons/9 inputs/1 form, no blank screen or error boundary); exact heading "Start a fetch / backfill job" present; `data-testid="readiness-badge"` read `data-state="ready"` | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-01-result.png` |
| UT-02 | Happy-path "Refreshed: …" includes forward aggregates | happy-path | P1 | Job reaches terminal state; "Refreshed: …" lists "forward aggregates" among categories | Started a real backfill (pre-filled 2005-06-16 → 2005-06-22, "Backfill snapshots" default), waited ~19m43s through the finalize tail; job reached `data-testid="job-status"` = **"ok"**; `data-testid="aggregates-refreshed"` read **"Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, factor lab all, drawdown expectations"** — "forward aggregates" present, no category dropped vs. the pre-iter-55 shape | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-02-result.png` |
| UT-03 | Job form stays blocked on incomplete dates | validation | P2 | "Start" button disabled with incomplete date pair | Real keyboard Backspace on the end-date field (see note below) left it empty; submit button read `disabled=true`, `opacity:0.5`, `cursor:not-allowed` | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-03-result.png` |
| UT-04 | Health badge/banner stability during forward-aggregate warm | error | P1 | Graded per Addendum 19's disclosed baseline, not a hard zero bar; flip-and-recover tolerated, a non-recovering flip or a false-"ready" would fail it | Live 459-poll `GET /api/health` drill (~19m43s, 03:06:46–03:26:29) spanning the SAME job's full run incl. finalize tail: **0/459 non-answers, 0/459 polls > 2.0s**, max latency 1.71s. `readiness-badge` stayed `data-state="ready"` at every check; `preflight-banner` stayed `data-verdict="DEGRADED"` (a live-vs-seed drift disclosure, unrelated to backend health) throughout — never flipped to backend-unavailable/NO-GO | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-result.png` + raw drill log `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-health-poll.log` |
| UT-05 | `/backtest` scorecard/evidence unaffected | regression | P1 | Real numeric rows, no placeholders | Scorecard: "Market Regime — Risk-on 66.07/100", real Candidate Counts (Actionable 0, Breakout-watch 54, …). Evidence section: "Snapshots contributing (≤ 2026-08-03): 2879", "Mean stock fwd return (60d): +3.74% (n=1249948)", "Mean max drawdown (60d): -15.53%" — all real numbers, no "—"/spinner | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-05-result.png` |
| UT-06 | Background compute panel unaffected (J-09 surface) | regression | P2 | Panel shows in-flight/last-outcome entry; footer text unchanged | Clicked "Previous available date" (`data-testid="asof-step-prev"`) x2 on `/backtest`, then `/data`: `data-testid="background-compute-panel"` showed an active in-flight entry ("as-of 2026-07-30 · elapsed 2.8s · horizons 0/5 · dataset r2940-f6541470") and the exact footer text "Since the last backend restart — this history is process-lifetime only, never persisted." | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-06-result.png` |
| UT-07 | Badge/banner render consistently across pages (ux) | ux | P2 | Same `data-state`/banner presence on Dashboard, Data Manager, Backtest | `readiness-badge` read `data-state="ready"` on all 3 pages; `preflight-banner` read `data-verdict="DEGRADED"` identically on all 3 pages | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-07-result.png` |

All P1 tests (UT-01, UT-02, UT-04, UT-05) pass. Both P2 tests (UT-03, UT-06/UT-07) pass.

---

## Passed Tests

### UT-01 — `/data` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-01-result.png`
- Navigated to `/data`; page rendered a full interactive form (not blank/error-boundary). Confirmed via DOM extraction the heading "Start a fetch / backfill job" is present verbatim, and `[data-testid="readiness-badge"]` carries `data-state="ready"`.
- Note: this Chrome MCP tool's console-log capture is a documented no-op ("`# TODO: Console logging not yet implemented`" in every `*-console.txt` sidecar file this run) — console-error absence could not be independently confirmed through that channel. Absence of any visual error/boundary state and a fully-populated, interactive DOM was used as the practical substitute.

### UT-02 — Happy-path "Refreshed: …" includes forward aggregates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-02-result.png`
- Left the pre-filled Start/End dates (2005-06-16 → 2005-06-22) and default "Job kind" = "Backfill snapshots" as-is, clicked Start.
- The per-date backfill stage finished in 44.4s (5/5 dates, 4115 forward returns inserted), then the job entered its finalize tail — the frontend itself disclosed this honestly ("updated 4m 33s ago · possibly stalled" — a real, non-fabricated staleness caveat, not a false "still ticking" claim).
- Polled every few minutes; job reached `job-status` = "ok" after ~19m43s total.
- `aggregates-refreshed` read: "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, factor lab all, drawdown expectations" — "forward aggregates" is present, confirming the iter-55 honest-status fix did not regress the all-horizons-complete success path.
- Screenshot note: the Job Progress card sits roughly 20,000px down this specific page load (a very tall `/data` render this session, likely from an expanded drift-warning ticker list), and a screenshot taken at that scroll depth rendered fully blank on 3 separate attempts (confirmed not a content issue — `getBoundingClientRect` showed the target element genuinely in-viewport each time) — a Chrome MCP screenshot-capture limitation at extreme scroll offsets, not a product defect. The exact "Refreshed: …" text above was captured via direct DOM extraction instead, which is the load-bearing evidence for this test; the attached screenshot documents the page's general rendered (non-broken) state.

### UT-03 — Job form stays blocked with an incomplete/invalid date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-03-result.png`
- First attempt (setting `.value = ''` + dispatching synthetic `input`/`change` events) did NOT trip the disabled state — the end-date field is a masked text input (`type="text"`, `inputmode="numeric"`, placeholder `yyyy-MM-dd`), and its validation only recomputes on genuine keyboard events, not synthetic DOM events. Recognized this as a test-technique gap, not a product finding, and redid it with real `Backspace` keypresses.
- With the field genuinely cleared via keyboard: `Start` button read `disabled=true`, computed `opacity:0.5`, `cursor:not-allowed` — matches the expected result exactly.

### UT-04 — Health badge/banner stability during forward-aggregate warm
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-result.png`, raw log `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-health-poll.log`
- Ran a live `GET /api/health` poll drill (~2s cadence) for the full duration of the UT-02 job, from "running" through the finalize tail into "ok": **459 polls, 03:06:46–03:26:29 (19m43s), 459/459 HTTP 200, 0 non-answers, 0 polls slower than the 2.0s BCW ceiling**, max latency 1.71s (elevated mid-run to ~0.4–1.4s during what is almost certainly the `forward_aggregates_warm` phase, but never timed out or refused).
- `readiness-badge` read `data-state="ready"` at every DOM check across the whole window. `preflight-banner` read `data-verdict="DEGRADED"` consistently (a live-vs-seed drift disclosure — unrelated to backend health) — it never flipped to a backend-unavailable/NO-GO state.
- Per the test plan's own grading rule, this counts as a clean PASS (no flip at all, let alone a non-recovering one or a false-"ready"). Context, stated honestly: this run's job was a single small 5-trading-day backfill without the concurrent heavy research-load condition the developer's own live drill (`reports/perf-budgets.md` Addendum 19) deliberately introduced — that drill's 11 non-answers were specifically attributed to cross-request GIL contention with a concurrent `compute_factor_lab_all`/`compute_factor_combination` request, a condition this lighter run did not reproduce. This result does not contradict or supersede Addendum 19 — it is additional, genuine evidence that the base path (no concurrent heavy research load) stays fully responsive.

### UT-05 — `/backtest` scorecard and evidence section are unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-05-result.png`
- Scorecard: "Market Regime — Risk-on 66.07 / 100", real Candidate Counts (Actionable 0, Breakout-watch 54, Pullback-watch 2, Extended 8, Avoid 475).
- Evidence section: "Snapshots contributing (≤ 2026-08-03): 2879", "Mean stock fwd return (60d): +3.74% (n=1249948)", "Mean max drawdown (60d): -15.53%" — real numeric values throughout, no placeholder dashes and no cold-recompute spinner.

### UT-06 — `/data`'s Background compute panel still reflects in-flight/last-outcome activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-06-result.png`
- Clicked "Previous available date" (`data-testid="asof-step-prev"`) twice on `/backtest`, then navigated to `/data`.
- `background-compute-panel` showed an active in-flight entry: "as-of 2026-07-30 · elapsed 2.8s · horizons 0/5 · dataset r2940-f6541470", and the footer text "Since the last backend restart — this history is process-lifetime only, never persisted." is present, unchanged.

### UT-07 — Readiness badge/banner render consistently across all pages
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-55-evidence/UT-07-result.png`
- Dashboard (`/`), Data Manager (`/data`), Backtest (`/backtest`): `readiness-badge` = `data-state="ready"` on all three; `preflight-banner` = `data-verdict="DEGRADED"` identically on all three (the same live-vs-seed drift state visible throughout this run, not a quiet "GO" state, but rendered consistently everywhere as required).

---

## Failed Tests

None.

---

## Skipped Tests

None — the infrastructure blocker from the earlier pass of this dispatch was fixed by the coordinator; both services were verified live before and after this full run.

---

## Note on golden replay scripts for J-05 / J-07 (target journeys)

`runs/goal-session-ops-hardening/journey-scripts/J-05.json` and `.../J-07.json` already exist, are
purpose-built (J-05 requires rotating to a fresh never-snapshotted trading day each use and a 19-minute
`wait_for` sized from live measurement; J-07 is a fast deterministic surface check with an explicit note
that the full live-warm behavior is proven by the drill/addendum, not by Playwright replay), and both
already produced a real, fresh PASS earlier in this same iteration via `demo_runner.py --mode verify`
(dev handoff: "J-05.json and J-07.json executed via the regression-replay lane for the first time this
session — both PASS"). UT-02 and UT-04 above independently re-confirm the same two underlying behaviors
live (a real backfill job completing with "forward aggregates" honestly reported; health staying
responsive through the same job's finalize tail) using this iteration's own dates and this dispatch's own
drill — but via manual UI-test-plan steps, not the journeys' own script contract (different target date,
no single-use-date rotation, no `stage-timings`/`scanner-runs` follow-through). Overwriting the existing,
more rigorous goldens with a rougher version derived from my manual steps would be a downgrade, not an
update, so I left both files untouched. No golden script changes were made this dispatch.

---

## Environment

- **Frontend URL:** http://localhost:3255 (HTTP 200 throughout)
- **Backend URL:** http://localhost:8255/api/health (HTTP 200 throughout this pass — confirmed at start, continuously via the UT-04 drill, and at the end)
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-10
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-55-evidence/`
