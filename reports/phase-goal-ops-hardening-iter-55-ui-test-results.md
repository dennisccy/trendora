# UI Test Results (merged)

**Date:** 2026-08-10
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 12/12 journeys passed (0 skipped, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-55-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-55-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-55-evidence/J-04-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-55-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-55-evidence/J-09-verify.png |
| UT-01 | `/data` loads without errors (smoke) | smoke | P1 | Page renders, "Start a fetch / backfill job" panel visible, readiness pill `data-state="ready"`, no console errors | Page rendered fully (82 buttons/9 inputs/1 form, no blank screen or error boundary); exact heading "Start a fetch / backfill job" present; `data-testid="readiness-badge"` read `data-state="ready"` | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-01-result.png` |
| UT-02 | Happy-path "Refreshed: …" includes forward aggregates | happy-path | P1 | Job reaches terminal state; "Refreshed: …" lists "forward aggregates" among categories | Started a real backfill (pre-filled 2005-06-16 → 2005-06-22, "Backfill snapshots" default), waited ~19m43s through the finalize tail; job reached `data-testid="job-status"` = **"ok"**; `data-testid="aggregates-refreshed"` read **"Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, factor lab all, drawdown expectations"** — "forward aggregates" present, no category dropped vs. the pre-iter-55 shape | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-02-result.png` |
| UT-03 | Job form stays blocked on incomplete dates | validation | P2 | "Start" button disabled with incomplete date pair | Real keyboard Backspace on the end-date field (see note below) left it empty; submit button read `disabled=true`, `opacity:0.5`, `cursor:not-allowed` | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-03-result.png` |
| UT-04 | Health badge/banner stability during forward-aggregate warm | error | P1 | Graded per Addendum 19's disclosed baseline, not a hard zero bar; flip-and-recover tolerated, a non-recovering flip or a false-"ready" would fail it | Live 459-poll `GET /api/health` drill (~19m43s, 03:06:46–03:26:29) spanning the SAME job's full run incl. finalize tail: **0/459 non-answers, 0/459 polls > 2.0s**, max latency 1.71s. `readiness-badge` stayed `data-state="ready"` at every check; `preflight-banner` stayed `data-verdict="DEGRADED"` (a live-vs-seed drift disclosure, unrelated to backend health) throughout — never flipped to backend-unavailable/NO-GO | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-result.png` + raw drill log `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-health-poll.log` |
| UT-05 | `/backtest` scorecard/evidence unaffected | regression | P1 | Real numeric rows, no placeholders | Scorecard: "Market Regime — Risk-on 66.07/100", real Candidate Counts (Actionable 0, Breakout-watch 54, …). Evidence section: "Snapshots contributing (≤ 2026-08-03): 2879", "Mean stock fwd return (60d): +3.74% (n=1249948)", "Mean max drawdown (60d): -15.53%" — all real numbers, no "—"/spinner | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-05-result.png` |
| UT-06 | Background compute panel unaffected (J-09 surface) | regression | P2 | Panel shows in-flight/last-outcome entry; footer text unchanged | Clicked "Previous available date" (`data-testid="asof-step-prev"`) x2 on `/backtest`, then `/data`: `data-testid="background-compute-panel"` showed an active in-flight entry ("as-of 2026-07-30 · elapsed 2.8s · horizons 0/5 · dataset r2940-f6541470") and the exact footer text "Since the last backend restart — this history is process-lifetime only, never persisted." | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-06-result.png` |
| UT-07 | Badge/banner render consistently across pages (ux) | ux | P2 | Same `data-state`/banner presence on Dashboard, Data Manager, Backtest | `readiness-badge` read `data-state="ready"` on all 3 pages; `preflight-banner` read `data-verdict="DEGRADED"` identically on all 3 pages | PASS | `reports/qa/goal-ops-hardening-iter-55-evidence/UT-07-result.png` |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-10

