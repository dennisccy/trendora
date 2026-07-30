# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-35-evidence/J-09-verify.png |
| UT-J-06 | Pages load only what they need (this iteration's scope: 4 sibling research labs render the shared computing/error/retry panel) | regression + new-capability | P1 | `phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` all render `resolveLabLoadPanel`'s labelled "still computing" state on a slow load and a retryable error card on failure, identical to Regime Lab | All 4 pages load and render correct data (functionally fine), but source inspection + live DOM confirm none of the 4 wire `resolveLabLoadPanel`: `FactorLabPage` (`_labs.tsx:311`) and `PhaseSeverityLabPage` (`_labs.tsx:4560`) still render the bare unlabelled `LabSkeleton` on loading; `RegimePhaseFactorPage` uses its own separate `CombinationSkeleton`; `SeverityVelocityPage` (`severity-velocity/page.tsx:90`) also renders bare `LabSkeleton`. All 4 call `ResearchError` **without** an `onRetry` prop (`_labs.tsx:312,4267→4269 is the ONLY onRetry call site (Regime Lab)`, `_labs.tsx:4561`, `_labs.tsx:4995`, `severity-velocity/page.tsx:92`), so none render a Retry button — only Regime Lab (`RegimeLabPage`, `_labs.tsx:4221-4269`) has the wiring. Dev handoff confirms: "Evidence-only iteration: no code changes were planned or made." | FAIL | `reports/qa/goal-ops-hardening-iter-35-evidence/J-06-phase-severity-lab.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression + risk | P1 | `/api/health` stays HTTP 200 throughout a full-horizon forward-aggregate warm with no frozen window; VmPeak stays under `server.memory_cap_mb` with a margin that does not regress from iter-34's measured margin; an induced memory-pressure abort is caught honestly with the same process still serving | `/api/health` DID stay HTTP 200 for the entire observation window (240/240 1 Hz polls over 4 continuous minutes, zero failures, zero 5xx) and the readiness badge stayed truthful throughout ("Ready · background compute running (5)"), and `/backtest?asof=2025-06-15` rendered the honest "Refreshing — showing the last complete evidence" banner with full prior-date evidence tables, never blank. BUT: VmPeak climbed from an already-elevated ~5.35 GB baseline (this same long-lived process had already run a real 283-date backfill via the J-01/J-03 regression replay before this test) all the way to **exactly the declared cap, 6,291,456 kB (6144 MB) — zero remaining margin at peak** — while 5 concurrent forward-aggregate warms I triggered were in flight, and **2 of those 5 background warm dispatches genuinely failed with a raw `MemoryError`** (self-healing/non-fatal per the existing `historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch...)` handler, no client-visible 5xx) inside `compute_forward_aggregates` → `_factor_observations` (`research.py:308`, itself already `yield_per`-batched). This is a stark regression from iter-34's reported "VmPeak plateaued at 2,691,732 kB... ample margin, zero measurable growth." Process never crashed and kept serving `/api/health` 200 throughout, including immediately after both MemoryErrors — so the "never wedged" sub-criterion held, but the "margin does not regress" sub-criterion did not. | FAIL | `reports/qa/goal-ops-hardening-iter-35-evidence/J-07-result.png` |

## Failed Tests

### UT-J-06 — Pages load only what they need (this iteration's scope: 4 sibling research labs render the shared computing/error/retry panel)

**Verdict:** FAIL
**Failure:** All 4 pages load and render correct data (functionally fine), but source inspection + live DOM confirm none of the 4 wire `resolveLabLoadPanel`: `FactorLabPage` (`_labs.tsx:311`) and `PhaseSeverityLabPage` (`_labs.tsx:4560`) still render the bare unlabelled `LabSkeleton` on loading; `RegimePhaseFactorPage` uses its own separate `CombinationSkeleton`; `SeverityVelocityPage` (`severity-velocity/page.tsx:90`) also renders bare `LabSkeleton`. All 4 call `ResearchError` **without** an `onRetry` prop (`_labs.tsx:312,4267→4269 is the ONLY onRetry call site (Regime Lab)`, `_labs.tsx:4561`, `_labs.tsx:4995`, `severity-velocity/page.tsx:92`), so none render a Retry button — only Regime Lab (`RegimeLabPage`, `_labs.tsx:4221-4269`) has the wiring. Dev handoff confirms: "Evidence-only iteration: no code changes were planned or made."
**Evidence:** ``reports/qa/goal-ops-hardening-iter-35-evidence/J-06-phase-severity-lab.png``

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** FAIL
**Failure:** `/api/health` DID stay HTTP 200 for the entire observation window (240/240 1 Hz polls over 4 continuous minutes, zero failures, zero 5xx) and the readiness badge stayed truthful throughout ("Ready · background compute running (5)"), and `/backtest?asof=2025-06-15` rendered the honest "Refreshing — showing the last complete evidence" banner with full prior-date evidence tables, never blank. BUT: VmPeak climbed from an already-elevated ~5.35 GB baseline (this same long-lived process had already run a real 283-date backfill via the J-01/J-03 regression replay before this test) all the way to **exactly the declared cap, 6,291,456 kB (6144 MB) — zero remaining margin at peak** — while 5 concurrent forward-aggregate warms I triggered were in flight, and **2 of those 5 background warm dispatches genuinely failed with a raw `MemoryError`** (self-healing/non-fatal per the existing `historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch...)` handler, no client-visible 5xx) inside `compute_forward_aggregates` → `_factor_observations` (`research.py:308`, itself already `yield_per`-batched). This is a stark regression from iter-34's reported "VmPeak plateaued at 2,691,732 kB... ample margin, zero measurable growth." Process never crashed and kept serving `/api/health` 200 throughout, including immediately after both MemoryErrors — so the "never wedged" sub-criterion held, but the "margin does not regress" sub-criterion did not.
**Evidence:** ``reports/qa/goal-ops-hardening-iter-35-evidence/J-07-result.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

