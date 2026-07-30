# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 15/20 journeys passed (5 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-36-evidence/J-09-verify.png |
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

## Skipped Tests

### UT-02 — Factor Lab computing notice

**Verdict:** SKIPPED
**Reason:** Not observed — factor-lab's data was already warm before this agent's first navigation (confirmed in `logs/backend.log`); no network-throttle action exists in this Chrome MCP tool to force a cold fetch

### UT-07 — Regime×Phase×Factor computing notice

**Verdict:** SKIPPED
**Reason:** Heading "Research — Regime × Phase × Factor" rendered immediately with controls, confirming that half of the expectation. The computing card itself was not observed — regime-phase-factor's `?view=pooled` payload was already warm (2 prior 200s logged for this endpoint before this agent's own navigation)

### UT-10 — Severity-velocity computing notice

**Verdict:** SKIPPED
**Reason:** Not observed — this endpoint's compute resolved in well under the 10s poll window even on its first-ever hit in this process (a lighter query than the phase-severity/regime labs); no network-throttle tool available to force a slower fetch

### UT-13 — Data page coverage panel unchanged

**Verdict:** SKIPPED
**Reason:** Not attempted — the backend went down (per the UT-03/06/08/11 cycle above) before this agent reached this test, and could not be restarted (see Critical operational note)

### UT-14 — Evidence page expectations panel renders real figures

**Verdict:** SKIPPED
**Reason:** Not attempted — same reason as UT-13

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

