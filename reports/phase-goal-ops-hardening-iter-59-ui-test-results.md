# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 9/12 journeys passed (3 skipped, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01: Backfill honors the requested range and explains zero-work (goal-mode regression journey, replay-flagged) | regression | P1 | See journey Acceptance below | All 8 acceptance points confirmed live (see Journey section) | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-J-01-result.png`, `UT-J-01-fullrange-result.png`, `UT-J-01-weekend-zerowork-crop.png` |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-evidence/J-09-verify.png |
| UT-01 | Page loads under normal conditions | smoke | P1 | Heading + both tables visible, correct column order, no error card | Heading "Research — Regime Lab" visible; `regime-lab-by-label` and `regime-lab-by-decile` cards present; column order Fwd 1d/5d/10d/20d/60d then MDD 1d/5d/10d/20d/60d in both tables; no error card | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-01-result.png` |
| UT-02 | Memory-pressure degrade renders honestly | happy-path | P1 | Backend restarted w/ `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`, all cells show NA + specific tooltip | Not executed — requires a backend restart, which this agent's hard rule ("never debug or restart the app") forbids; the test plan's own precondition explicitly allows this skip ("skip this test if you only have browser access") | SKIP | none |
| UT-03 | Rank-IC row keeps old NA tooltip (known gap) | validation | P2 | With fault-injected backend still running, Rank-IC NA cell keeps old generic tooltip | Not executed — depends on UT-02's fault-injected backend state, which was never established (same restart restriction) | SKIP | none |
| UT-04 | Fully-down backend shows generic error card | error | P2 | Backend stopped entirely; red "Backend unavailable" card + Retry button appear | Not executed — requires stopping the backend entirely, which this agent's hard rule forbids | SKIP | none |
| UT-05 | Normal figures unchanged from before this phase | regression | P1 | UI value/`n=` matches raw API; no `regime_lab_status`/`status` keys in response; sort + N= chip still work | `GET /api/research/regime-lab?view=pooled` (the exact query the frontend sends — `REGIME_LAB_VIEW="pooled"`) returned `by_label[0]` ("Strong risk-on") horizon 20 `mean_return=0.0035029...` (rounds to +0.35%, `n=282050`) — byte-for-byte match to the rendered "Strong risk-on / Fwd 20d" cell; no `regime_lab_status` key anywhere in the payload and no `status` key on any `by_horizon[]` entry (checked all `by_label` + `by_decile` rows); clicking the "Fwd 20d" header re-sorted rows descending (2.48% → 2.27% → 2.22% → 1.42% → 1.07% → 0.35%); an "N=" chip is an `<a target="_blank" href="/research/samples?kind=regime-lab&horizon=1&slice=label&view=pooled&regime=Defensive">`, clicked and confirmed the samples page opened in a new tab with matching cohort content ("Defensive") | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-05-result.png` |
| UT-06 | Regime Lab still reachable from Research index | ux | P3 | Card titled "Regime Lab" with matching description text; navigates to `/research/regime-lab`; no new degraded/unavailable badge | `[data-testid="research-lab-link-regime-lab"]` present on `/research`, text "Regime Lab" + "How have stocks' forward returns and downside risk differed across market regimes? ..." (no badge/icon added); clicking it navigated to `/research/regime-lab` (confirmed via `await_text` on the page heading) | PASS | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-06-result.png` |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Skipped Tests

### UT-02 — Memory-pressure degrade renders honestly

**Verdict:** SKIPPED
**Reason:** Not executed — requires a backend restart, which this agent's hard rule ("never debug or restart the app") forbids; the test plan's own precondition explicitly allows this skip ("skip this test if you only have browser access")

### UT-03 — Rank-IC row keeps old NA tooltip (known gap)

**Verdict:** SKIPPED
**Reason:** Not executed — depends on UT-02's fault-injected backend state, which was never established (same restart restriction)

### UT-04 — Fully-down backend shows generic error card

**Verdict:** SKIPPED
**Reason:** Not executed — requires stopping the backend entirely, which this agent's hard rule forbids

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

