# Phase goal-ops-hardening-iter-35 — UI Test Results

**Phase:** goal-ops-hardening-iter-35
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 0/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Pages load only what they need (this iteration's scope: 4 sibling research labs render the shared computing/error/retry panel) | regression + new-capability | P1 | `phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` all render `resolveLabLoadPanel`'s labelled "still computing" state on a slow load and a retryable error card on failure, identical to Regime Lab | All 4 pages load and render correct data (functionally fine), but source inspection + live DOM confirm none of the 4 wire `resolveLabLoadPanel`: `FactorLabPage` (`_labs.tsx:311`) and `PhaseSeverityLabPage` (`_labs.tsx:4560`) still render the bare unlabelled `LabSkeleton` on loading; `RegimePhaseFactorPage` uses its own separate `CombinationSkeleton`; `SeverityVelocityPage` (`severity-velocity/page.tsx:90`) also renders bare `LabSkeleton`. All 4 call `ResearchError` **without** an `onRetry` prop (`_labs.tsx:312,4267→4269 is the ONLY onRetry call site (Regime Lab)`, `_labs.tsx:4561`, `_labs.tsx:4995`, `severity-velocity/page.tsx:92`), so none render a Retry button — only Regime Lab (`RegimeLabPage`, `_labs.tsx:4221-4269`) has the wiring. Dev handoff confirms: "Evidence-only iteration: no code changes were planned or made." | FAIL | `reports/qa/goal-ops-hardening-iter-35-evidence/J-06-phase-severity-lab.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression + risk | P1 | `/api/health` stays HTTP 200 throughout a full-horizon forward-aggregate warm with no frozen window; VmPeak stays under `server.memory_cap_mb` with a margin that does not regress from iter-34's measured margin; an induced memory-pressure abort is caught honestly with the same process still serving | `/api/health` DID stay HTTP 200 for the entire observation window (240/240 1 Hz polls over 4 continuous minutes, zero failures, zero 5xx) and the readiness badge stayed truthful throughout ("Ready · background compute running (5)"), and `/backtest?asof=2025-06-15` rendered the honest "Refreshing — showing the last complete evidence" banner with full prior-date evidence tables, never blank. BUT: VmPeak climbed from an already-elevated ~5.35 GB baseline (this same long-lived process had already run a real 283-date backfill via the J-01/J-03 regression replay before this test) all the way to **exactly the declared cap, 6,291,456 kB (6144 MB) — zero remaining margin at peak** — while 5 concurrent forward-aggregate warms I triggered were in flight, and **2 of those 5 background warm dispatches genuinely failed with a raw `MemoryError`** (self-healing/non-fatal per the existing `historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch...)` handler, no client-visible 5xx) inside `compute_forward_aggregates` → `_factor_observations` (`research.py:308`, itself already `yield_per`-batched). This is a stark regression from iter-34's reported "VmPeak plateaued at 2,691,732 kB... ample margin, zero measurable growth." Process never crashed and kept serving `/api/health` 200 throughout, including immediately after both MemoryErrors — so the "never wedged" sub-criterion held, but the "margin does not regress" sub-criterion did not. | FAIL | `reports/qa/goal-ops-hardening-iter-35-evidence/J-07-result.png` |

---

## Passed Tests

None.

---

## Failed Tests

### UT-J-06 — Pages load only what they need (4 sibling labs' computing/error/retry wiring)
**Verdict:** FAIL
**Failure:** The iteration's own scope ("Wire the already-generic, already-exported `resolveLabLoadPanel` into the 4 sibling research lab pages... exactly as it is already wired for Regime Lab") was not implemented. This iteration's dev handoff (`docs/handoffs/goal-ops-hardening-iter-35-dev.md`) states plainly: "Evidence-only iteration: no code changes were planned or made." Confirmed independently by reading `apps/frontend/app/research/_labs.tsx` and `apps/frontend/app/research/severity-velocity/page.tsx`:
- `FactorLabPage` (`/research/factor-lab`) — line 311: `{state.kind === "loading" ? <LabSkeleton /> : null}` (bare skeleton, no computing label); line 312: `<ResearchError what="The Factor-Lab evidence" />` (no `onRetry`).
- `PhaseSeverityLabPage` (`/research/phase-severity-lab`) — line 4560/4561: same bare-skeleton + no-retry pattern.
- `RegimePhaseFactorPage` (`/research/regime-phase-factor`) — uses its own separate `CombinationSkeleton` (not `LabSkeleton`/`resolveLabLoadPanel`); its error card (line ~4990-4998) has no Retry button.
- `SeverityVelocityPage` (`/research/severity-velocity`, its own file) — line 90-93: same bare-skeleton + no-retry pattern.
- Only `RegimeLabPage` (`/research/regime-lab`, `_labs.tsx:4221-4269`) calls `resolveLabLoadPanel` and passes `onRetry={() => setAttempt((previous) => previous + 1)}` to `ResearchError`.

`grep -n "Retry\|retry"` over the 4 sibling route files returns zero hits inside their own component bodies (the only "Retry" hits in `_labs.tsx` are the `ResearchError` component definition itself and Regime Lab's own call site).

**Evidence:** `reports/qa/goal-ops-hardening-iter-35-evidence/J-06-phase-severity-lab.png`, `J-06-factor-lab.png`, `J-06-regime-phase-factor.png`, `J-06-severity-velocity.png` (all 4 pages load and render real data correctly on this warm backend — the FAIL is specifically the missing shared loading/error/retry wiring, not broken data rendering)

**Steps taken:**
1. Navigated to `/research/regime-lab` (reference — confirmed already wired) → screenshot, page renders fine.
2. Navigated to `/research/phase-severity-lab`, `/research/factor-lab`, `/research/regime-phase-factor`, `/research/severity-velocity` — each renders correct evidence tables (functionally healthy) but on a warm/fast backend none naturally enters a loading/error state to observe live; source-level inspection (above) is the definitive evidence since the wiring is a structural fact, not a transient state.
3. Confirmed via the dev handoff and `git diff apps/frontend/app/research/_labs.tsx` (empty diff vs HEAD) that no frontend code changed this iteration.

**Expected:** All 4 sibling labs show the labelled "Still computing — Ns elapsed" card on a slow load and a working Retry control on error, per the iteration's Definition of Done and TC-5/TC-6.
**Actual:** All 4 sibling labs still use their pre-iteration bare-skeleton / non-retryable error presentation; only Regime Lab has the shared panel.

---

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** FAIL
**Failure:** The VmPeak-margin acceptance criterion regressed sharply and, under real (not artificially induced) concurrent warm load, the working long-lived backend process hit its declared memory cap exactly and threw two genuine `MemoryError`s from inside the canonical forward-aggregate computation path.

**Evidence:** `reports/qa/goal-ops-hardening-iter-35-evidence/J-07-result.png` (full-page backtest evidence + honest "Refreshing" banner, badge "Ready · background compute running (5)"), `reports/qa/goal-ops-hardening-iter-35-evidence/J-07-warming-state.png` (badge mid-warm)

**Steps taken:**
1. **Trigger the warm, in the SAME long-lived process (PID 2351049, backend port 8255):** confirmed at rest the badge read "Ready" with no active background compute (`GET /api/health`). Triggered `GET /api/backtest?as_of=<date>` for several confirmed-uncached dates while hunting for a genuinely cold as-of (most dates were already warm from this iteration's own regression-replay backfill and prior iterations' testing on the unchanged `dataset_version`). Four small-universe historical dates (1996, 1999, 2001, 2005) completed a real 5-horizon warm in ~4.2 s each with zero VmPeak growth. Four modern full-universe dates (2025-06-15, 2025-08-05, 2025-09-22, 2025-11-10) plus one more (2025-12-08) then ran **concurrently** (I could not find a single uncached modern date without triggering several while searching) — a heavier-than-canonical 5-way-parallel version of "trigger the warm," but still a legitimate exercise of the exact `_refresh_ingest_aggregates`/`ensure_historical_forward_aggregates_dispatched` warm path this journey targets, in the one real backend process.
2. **Poll `GET /api/health` at 1 Hz throughout:** ran a 240-second, 1 Hz poll loop spanning the bulk of the concurrent warm. **Result: 240/240 HTTP 200, zero failures, zero 5xx anywhere in the backend log for this process's session.** Latency stayed in the 0.13-0.71 s range (occasional spikes under the 5-way concurrent load; exceeds the ≤0.1 s budget — consistent WARN under load, not a functional failure, per the established convention). Navigated the browser live to `/` mid-warm: badge read **"Ready" + "background compute running (5)"** — honest, never blank/crashed. Navigated to `/backtest?asof=2025-06-15` mid-warm: the page rendered full prior-date (2025-05-30) evidence tables with the honest banner *"Refreshing — showing the last complete evidence... This date's own evidence is being computed in the background... no partial or fabricated figures are shown"* — never blank, matching the honest-status requirement (screenshot: `J-07-result.png`).
3. **VmPeak margin:** `/proc/<pid>/status` polled alongside every health check. VmPeak started this test session at 5,353,968 kB (already elevated — this same process had run a real 283-date backfill, `POST /api/data/jobs`, moments earlier via the J-01/J-03 golden-replay lane before my session began) and **climbed steadily to exactly 6,291,456 kB — the full declared `server.memory_cap_mb=6144` cap, i.e. 0 kB of margin at peak** — while the 5 concurrent warms ran. This is a severe regression from iter-34's independently-measured "VmPeak plateaued at 2,691,732 kB against the 6,291,456 kB cap — ample margin, zero measurable growth from the warm itself" (`reports/perf-budgets.md`, "Iteration 34 — J-07 step 2"). Caveat: my measurement reflects 5 concurrent as-of warms (25 horizon-computations in flight at once) plus a preceding real backfill, not iter-34's presumably single isolated warm — a heavier scenario, but one that arose naturally while exercising step 1 as written, not a contrived stress test.
4. **Organic memory-pressure event (not the separate throwaway-process drill):** at the moment VmPeak hit the cap, **2 of the 5 in-flight background dispatches (`asof_key=2025-08-05`, `asof_key=2025-11-10`) failed with a genuine `MemoryError`**, raised from `compute_forward_aggregates` → `_forward_agg_slice_map` → `_factor_observations` (`apps/backend/app/engine/research.py:308`) while iterating an already-`yield_per`-batched SQLAlchemy cursor — i.e. even a chunked/bounded read failed once the process's overall virtual-memory ceiling was reached from concurrent load. The backend's own handler logged this as **"historical forward-aggregate background dispatch failed (non-fatal, will re-dispatch on the next request for this identity...)"** — self-healing, no client-visible 5xx, and `GET /api/health` kept returning 200 immediately after and repeatedly thereafter on the SAME PID (confirmed alive, `ELAPSED 22:24`, no restart). This is a genuinely positive finding for the "never wedged/never a restart requirement" sub-criterion, occurring for real rather than via an artificial throwaway-process drill — but it is also direct, first-hand proof that the memory-pressure failure mode this journey exists to guard against is currently reachable during **ordinary** step-1 warm activity, not just an induced edge case. I did not additionally launch a separate throttled-cap throwaway process for the classic "induced" drill (step 4's literal formulation) — that action is backend/process-level and not browser-drivable, matching iter-34's own browser-qa precedent, and doing so on top of an already-cap-saturated live process would have compounded real risk for no additional evidence value.

**Anti-goal check (AG-8/AG-10):** the process itself never crashed and the host was not put at risk (the kernel `ulimit -v` cap did its job — `MemoryError`s were contained inside the one process, never a host-wide event), but AG-8's "unbounded whole-table ORM loads are forbidden on the deep basis" is evidenced as **still live**: ledger finding iter-29/d (the whole-table `prefilled_bar_cache` load) was not fixed this iteration (dev handoff: no code changes), and this session's own numbers show why that matters — the process now runs with far less headroom than iter-34 measured.

**Expected:** VmPeak stays comfortably under the cap with a margin that does not regress from iter-34; no `MemoryError`s during ordinary warm-triggering.
**Actual:** VmPeak reached the exact cap (zero margin) and 2 background warm dispatches threw real `MemoryError`s (self-healing, no crash, no client-visible failure) during ordinary use of the same warm path this journey exercises.

---

## Skipped Tests

None. J-01, J-03, J-04, J-05, J-08, J-09 were explicitly excluded from this run's scope per the dispatch (verified separately by deterministic golden replay — see `reports/phase-goal-ops-hardening-iter-35-regression-replay-results.md`, 6/6 PASS) — not tested and not recorded as SKIPPED rows here.

---

## Golden Replay Script

None written this run. Per the dispatch instructions, a golden replay script is written only "for every journey you verify PASS." Both J-06 and J-07 failed this session, so no `journey-scripts/J-06.json` or `journey-scripts/J-07.json` update was made (the existing `J-06.json`/`J-07.json` files on disk are carried unchanged from the prior passing iteration and are not authoritative for this iteration's FAIL verdicts).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-35-evidence/`
- **Backend process:** PID 2351049 — confirmed alive, unrestarted, still serving `GET /api/health` 200 at the end of this session (including after 2 organic `MemoryError` events); VmPeak at session end: 6,291,456 kB (= declared `memory_cap_mb`, 0 kB margin at peak; VmRSS at session end ~5.79 GB and still climbing when observation stopped, with 3 of the 5 triggered warms still in flight)
