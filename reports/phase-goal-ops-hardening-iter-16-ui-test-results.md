# UI Test Results (merged)

**Date:** 2026-07-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 11/14 journeys passed (3 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-16-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-16-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-16-evidence/J-05-verify.png |
| UT-01 | `/backtest` loads, ready-state evidence renders | smoke | P1 | Page renders, "Backtest" heading, evidence section populated with all sub-panels, no refreshing/not-yet-computed cards, no console errors | Confirmed: readiness badge "Ready", as-of badge "Viewing as-of 2026-07-22 (latest)", `evidence-aggregate` section fully populated with all 8 sub-panel tables, no refreshing/empty-state text anywhere, console clean (only React DevTools info) | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-01-result.png`, `UT-01-top.png` |
| UT-02 | Refreshing banner appears during a live backfill | happy-path | P1 | Amber `evidence-refreshing` banner above the evidence section during a live single-day backfill, generation timestamp matches the pre-backfill value, evidence section stays fully populated | Started single-day backfill (2025-05-20, run id=150) at 21:53:46 UTC; by 21:55:29 UTC (~1m43s later) `/backtest` served `evidence_status="refreshing"` with banner text "Refreshing — showing the last complete evidence" + generation "2026-07-23 20:57:22" — byte-identical to the pre-backfill `evidence_generated_at`; evidence section below remained fully populated (8 tables, same figures as ready state) | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png`, `UT-02-job-running-top.png` |
| UT-03 | Not-yet-computed empty state (throwaway DB only) | happy-path | P2 | Dashed-border "Backtest evidence not yet computed" card in place of the evidence section | Not executed — per the pump note this DB is populated (every `asof_key` already has computed evidence) and reaching this state would require deleting `ForwardAggregateCache` rows, which is explicitly out of scope as destructive. Contract already proven by 10/10 passing unit tests in `test_forward_testing_serving_split.py` per the dev handoff | SKIPPED | none — operator/throwaway-DB action, not performed (by design) |
| UT-04 | Cutover back to ready after the warm completes | regression | P1 | Refreshing banner gone, evidence section shows new populated numbers, no empty state | Backfill job (id=150) reached `status=ok` at 21:59:49 UTC (~6m3s total) with `aggregates_refreshed` including `forward_aggregates`; `/backtest` reload showed `evidence_status="ready"` at a NEW `evidence_generated_at` ("2026-07-23T21:56:07.4"), refreshing banner gone, summary updated (1801 snapshots / n=744166, up from 1800 / n=743634 pre-backfill), no empty state | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-04-cutover-ready.png` |
| UT-05 | Ready-state sub-panels unchanged | regression | P1 | `evidence-summary` line + all 8 named sub-panel titles present, in order, unchanged | Confirmed `evidence-summary` reads "Snapshots contributing (≤ 2026-07-22): 1800 / As-of range: 2005-02-25 → 2026-04-24 / Mean stock fwd return (60d): +4.34% (n=743634) / Mean max drawdown (60d): -15.13%"; all 8 sub-panels present in the expected order (score bucket, excess vs benchmarks, setup type, market regime, VCP vs non-VCP, Pullback-to-DMA vs not, Flat-base vs not, control-group) | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-01-result.png` (= `UT-05-result.png`, identical capture) |
| UT-06 | Rest of page unaffected during non-ready states | regression | P2 | Survivorship bias / As-of scan summary / scorecard / Return attribution / Leadership cohorts all render normally while the evidence section shows refreshing | Confirmed on the same capture as UT-02: Survivorship bias card, Market Regime (61.86, Narrow leadership), Candidate Counts, Forward-test scorecard, Return attribution, Leadership cohorts (Top Sectors/Themes/Ranked cohort) all rendered identically to the ready-state capture — no skeleton, no error, no leakage of the refreshing treatment upward | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png` |
| UT-07 | Historical as-of viewing unaffected | regression | P2 | Badge shows historical date, evidence section reflects chosen date, no refreshing banner ever, first view slower (one-time compute), reload fast | Confirmed for 2026-07-10, 2026-07-13, 2026-07-14: badge correctly switches to "Viewing as-of `<date>` (historical)"; evidence-aggregate eventually renders fully populated and correct for each date; no refreshing banner ever appears for a historical date; a same-date reload is fast (< ~6s, mostly page-load overhead). **Note:** the first-view compute measured considerably longer than the test plan's "a few seconds" — see note below | PASS (with timing note) | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-07-historical.png`, `UT-07-timing-check.png` |
| UT-08 | Backend-unavailable error card intact | error | P2 | "Backend unavailable" card with no partial content when the API fails | Not executed — stopping the backend is a service action blocked this session (permission classifier / pump note: do not kill, restart, or start any service). The error-rendering code path (`state.kind === "error"` in `page.tsx`) is confirmed untouched by this iteration's diff (UI surface map: this iteration's change is confined to the evidence-section branch inside `BacktestResults`) — pre-existing, low-risk, unmodified path | SKIPPED | none — requires backend stop, not performed |
| UT-09 | Refreshing banner tone/discoverability | ux | P2 | Calm, factual banner text; amber tone matching other status cards; page stays fully interactive | Banner text is plain-language and understandable without backend knowledge; amber/warn border visually matches the "Survivorship bias" card's treatment (not red/danger); confirmed page stays interactive while the banner shows — clicked the "5d" Horizon selector button and the Return Attribution section re-rendered ("Open the 5-day forward return...") while the refreshing banner remained visible and unaffected | PASS | `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png` |
| UT-10 | Data-contract fields visible in Network tab | ux | P2 | `evidence_status` / `evidence_generated_at` / `evidence_by_horizon` present and consistent with on-screen state | Confirmed via direct fetch of `GET /api/backtest` from the page context in both states: ready (`evidence_status:"ready"`, `evidence_generated_at:"2026-07-23T20:57:22.7"`, 5 horizon keys, `is_latest:true`) and refreshing (`evidence_status:"refreshing"`, same `evidence_generated_at`, matching the on-screen banner) — both cross-checked against what was on-screen at the time | PASS | inline JSON in this report; screenshots above |
| UT-J-04 | J-04: Non-blocking boot with visible status (goal.md regression journey) | regression | P1 (journey) | Restart→≤5s health, initializing-phase badge, kill→crashed presentation, logfile evidence, restart→interrupted-job detection | Not executed — J-04's steps 1/3/4/6 require restarting and killing the backend process, which is explicitly blocked this session (pump note: "Do NOT kill, restart, or start any service"). Confirmed non-disruptively: backend currently healthy (`GET /api/health` 200, `readiness:"ready"`); persistent logfile `logs/backend.log` exists (41,241 lines) and contains boot-cycle entries (`=== start-backend.sh: launching at ... ===`, `Uvicorn running...`, `Application startup complete.`) across multiple historical restarts. This iteration's diff does not touch `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or `app/engine/warmup.py` (binding "Do not redo" per the phase spec's OUT OF SCOPE section) — pre-existing, unmodified code path, no new regression risk introduced this iteration | SKIPPED | `logs/backend.log` (read-only, not modified) |

## Skipped Tests

### UT-03 — Not-yet-computed empty state (throwaway DB only)

**Verdict:** SKIPPED
**Reason:** Not executed — per the pump note this DB is populated (every `asof_key` already has computed evidence) and reaching this state would require deleting `ForwardAggregateCache` rows, which is explicitly out of scope as destructive. Contract already proven by 10/10 passing unit tests in `test_forward_testing_serving_split.py` per the dev handoff

### UT-08 — Backend-unavailable error card intact

**Verdict:** SKIPPED
**Reason:** Not executed — stopping the backend is a service action blocked this session (permission classifier / pump note: do not kill, restart, or start any service). The error-rendering code path (`state.kind === "error"` in `page.tsx`) is confirmed untouched by this iteration's diff (UI surface map: this iteration's change is confined to the evidence-section branch inside `BacktestResults`) — pre-existing, low-risk, unmodified path

### UT-J-04 — J-04: Non-blocking boot with visible status (goal.md regression journey)

**Verdict:** SKIPPED
**Reason:** Not executed — J-04's steps 1/3/4/6 require restarting and killing the backend process, which is explicitly blocked this session (pump note: "Do NOT kill, restart, or start any service"). Confirmed non-disruptively: backend currently healthy (`GET /api/health` 200, `readiness:"ready"`); persistent logfile `logs/backend.log` exists (41,241 lines) and contains boot-cycle entries (`=== start-backend.sh: launching at ... ===`, `Uvicorn running...`, `Application startup complete.`) across multiple historical restarts. This iteration's diff does not touch `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or `app/engine/warmup.py` (binding "Do not redo" per the phase spec's OUT OF SCOPE section) — pre-existing, unmodified code path, no new regression risk introduced this iteration

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-23

