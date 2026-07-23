# Phase goal-ops-hardening-iter-16 — UI Test Results

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/8 executed tests passed (3 skipped, 0 failed) — all four P1 tests (UT-01, UT-02, UT-04, UT-05) PASS.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
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

---

## Passed Tests

### UT-01 — `/backtest` loads with the evidence section in its normal `ready` state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-01-result.png`, `UT-01-top.png`
- Readiness badge reads "Ready"; as-of badge reads "Viewing as-of 2026-07-22 (latest)".
- `data-testid="evidence-aggregate"` section titled "Forward-tested evidence (expanding window ≤ 2026-07-22)" fully populated with 8 sub-panel tables (score bucket, excess vs benchmarks, setup type, market regime, VCP vs non-VCP, Pullback-to-DMA vs not, Flat-base vs not, control-group comparison).
- No "Refreshing" or "not yet computed" text anywhere on the page.
- `get_console_messages` showed only the standard React DevTools info line — no errors mentioning `evidence_status`, `evidence_by_horizon`, or `evidence_generated_at`.

### UT-02 — Operator can see the "refreshing" disclosure during a live single-day backfill
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png`, `UT-02-job-running-top.png`
- Identified a genuinely unsnapshotted date (2025-05-20 — confirmed absent from `scanner_runs` via read-only DB query, and distinct from the 4 dates the pump note flagged as already used: 2025-05-21/22/28, 2026-07-21).
- Filled "Start date"/"End date" = 2025-05-20 on `/data`, left "Job kind" on default "Backfill snapshots", clicked Start. `data-testid="job-status"` read "running" with a spinning icon (confirmed via DOM; run id=150 confirmed server-side, started 21:53:46 UTC).
- Polling `/backtest`: by 21:55:29 UTC the page served the refreshing state. `data-testid="evidence-refreshing"` banner text: *"Refreshing — showing the last complete evidence / A newer dataset version is still being warmed. The forward-tested evidence below is the last complete version, generated 2026-07-23 20:57:22. This updates automatically once the new version finishes warming — no partial or fabricated figures are shown in the meantime."*
- The generation timestamp "2026-07-23 20:57:22" is byte-identical to the `evidence_generated_at` captured from the SAME page BEFORE the backfill started — confirming the banner honestly serves the last-good prior version, not something newer or mixed.
- The evidence section directly below remained fully populated (8 tables, identical figures to the pre-backfill ready state) — not blank, not a skeleton.
- Banner confirmed positioned immediately above the `evidence-aggregate` section (DOM order check), with a spinning icon (`.animate-spin` present).

### UT-04 — Cutover: refreshing banner disappears once the backfill's finalize warm completes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-04-cutover-ready.png`
- Polled `/data` until run id=150 reached `status="ok"` (21:59:49 UTC — total job duration ~6m3s, consistent with this iteration's own ~6.3min measurement for a single-day backfill).
- `data-testid="aggregates-refreshed"` read "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations" — includes forward aggregates.
- Reloaded `/backtest`: refreshing banner gone; `evidence_status` via direct API fetch is `"ready"` at a NEW `evidence_generated_at` ("2026-07-23T21:56:07.4", distinct from the pre-backfill "20:57:22.7"); `evidence-summary` updated to "Snapshots contributing (≤ 2026-07-22): 1801" / "n=744166" (up from 1800 / n=743634) — proving genuinely new, not stale, data; no not-yet-computed empty state.

### UT-05 — Ready-state evidence section renders all of its original sub-panels unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-01-result.png`
- `evidence-summary` text: "Snapshots contributing (≤ 2026-07-22): 1800 / As-of range: 2005-02-25 → 2026-04-24 / Mean stock fwd return (60d): +4.34% (n=743634) / Mean max drawdown (60d): -15.13% / Figures with n < 30 ⚠ are low-sample."
- All 8 sub-panels present, in order: Forward return by score bucket, Excess vs benchmarks, Forward return by setup type, Forward return by market regime, Forward return: VCP vs non-VCP, Forward return: Pullback-to-rising-DMA vs not, Forward return: Flat-base breakout vs not, Control-group comparison — selection vs sector beta. None missing, reordered, or replaced.

### UT-06 — Rest of `/backtest` page is unaffected while the evidence section is in a non-`ready` state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png`
- Captured during the same live refreshing window as UT-02. Survivorship bias card, Market Regime (61.86/100, "Narrow leadership"), Candidate Counts (Actionable 0 / Breakout-watch 54 / Pullback-watch 1), Forward-test scorecard, Return attribution, Leadership cohorts (Top Sectors, Top Themes, Ranked cohort table) all render identically to the ready-state capture (same figures) — no skeleton, no error card, no trace of the refreshing/empty-state treatment leaking above the evidence section.

### UT-07 — Historical as-of viewing is unaffected by this iteration's change
**Verdict:** PASS (see timing note)
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-07-historical.png`, `UT-07-timing-check.png`
- Tested against three previously-unviewed historical dates: 2026-07-10, 2026-07-13, 2026-07-14.
- Each time: as-of badge correctly switched to "Viewing as-of `<date>` (historical)" near-instantly; the "Forward-tested evidence (expanding window ≤ `<date>`)" section eventually rendered fully populated and numerically correct for that date (cross-checked `evidence-summary` snapshot counts/date ranges per date); no refreshing banner ever appeared for a historical date; a same-date reload was fast (~6s wall-clock in a clean measurement for 2026-07-14, most of which is ordinary page-load, vs. the much longer first-view compute — see note).
- **Timing note (honest observation, not a failure):** the test plan describes the first-view historical compute as taking "a few seconds longer" than the latest-date view. Measured directly (clean `eval` polling, no confounding parallel requests) for 2026-07-14: click confirmed at 23:06:52.57, `evidence-aggregate` first present at 23:08:15.82 — **≈83 seconds**, not "a few seconds." 2026-07-13 showed the same pattern (>60s across two chained 30s polls). This is explicitly an OUT-OF-SCOPE, pre-existing code path per this iteration's own phase spec (the historical lazy create-once-cache behavior is unchanged by iter-16 — confirmed in "OUT OF SCOPE" and the BACKGROUND "Scope note"), so it is not attributed to this iteration's diff and does not fail the test's actual assertions (all of which did eventually hold true), but is worth the product team's awareness as the ~30-year deep basis makes this lazy path meaningfully slower than before. (Separately noted: this session's `await_element` browser-automation action returned false negatives twice against a verified-present element — a tooling quirk, not a product issue; subsequent measurements used direct `querySelector` polling instead.)

### UT-09 — Refreshing banner reads as calm and factual, not alarming, and never blocks the page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-16-evidence/UT-02-refreshing-fullpage.png`
- Full banner text is plain-language and self-explanatory without backend knowledge (no cache keys, no function names; it does use the plain-English phrase "a newer dataset version" — judged as ordinary language, not internal jargon like the literal `dataset_version` field name, a cache key, or a function name).
- Amber/warn border-and-icon treatment visually matches the page's pre-existing "Survivorship bias" card styling — not a red/danger treatment.
- Interactivity confirmed: clicked the "5d" Horizon selector button while the banner was showing; the Return Attribution section's description text updated to "Open the 5-day forward return..." confirming the click was genuinely handled; the refreshing banner remained visible and unaffected throughout.

### UT-10 — Data contract: `evidence_status` and `evidence_generated_at` are present in the actual API response
**Verdict:** PASS
**Evidence:** inline JSON below; cross-referenced against `UT-01-result.png` and `UT-02-refreshing-fullpage.png`
- Ready state: `fetch('http://localhost:8255/api/backtest')` → `{"evidence_status":"ready","evidence_generated_at":"2026-07-23T20:57:22.711666","horizon_keys":["1","5","10","20","60"],"is_latest":true}` — matched the on-screen ready state (no banner, no empty state).
- Refreshing state (captured via curl during the live window, cross-checked against the on-screen banner moments later): `evidence_status:"refreshing"`, `evidence_generated_at:"2026-07-23T20:57:22.711666"` — the SAME timestamp the banner displayed ("2026-07-23 20:57:22"), and `evidence_by_horizon` was populated (the on-screen evidence section showed all 8 sub-panel tables at that same moment, which the API response backs).
- `evidence_by_horizon` in both cases carried all 5 configured horizon keys (1/5/10/20/60) — never `{}` outside the (unexercised, per UT-03) not-yet-computed case.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-03 — "Not yet computed" empty state when no evidence has ever been computed
**Verdict:** SKIPPED
**Reason:** Per the test plan's own precondition and the pump note, this DB is populated (every `asof_key` already has computed forward-aggregate evidence) and reaching `evidence_status=="not_yet_computed"` non-destructively would require a separate throwaway/freshly-seeded backend, which was not available this session and standing one up is a service action outside this test plan's scope. Not attempted, per explicit instruction not to delete `ForwardAggregateCache` rows or otherwise force this state destructively. The response-shape contract is already proven by 10/10 passing unit tests in `apps/backend/tests/test_forward_testing_serving_split.py` per the dev handoff (covered at the unit/API layer, not independently browser-verified this iteration).

### UT-08 — Backend-unavailable error card still shown when the API fails
**Verdict:** SKIPPED
**Reason:** Requires making the backend unreachable, which is a service-stop action explicitly blocked this session (permission classifier; pump note: "Do NOT kill, restart, or start any service"). The underlying error-rendering code path (`state.kind === "error"` in `page.tsx`) is confirmed untouched by this iteration's diff per the UI surface map (this iteration's change is confined to the evidence-section branch inside `BacktestResults`) — a low-risk, pre-existing path, not new code this iteration.

### UT-J-04 — J-04: Non-blocking boot with visible status (goal.md regression journey)
**Verdict:** SKIPPED
**Reason:** J-04's steps require restarting the backend twice and killing it once (steps 1, 3, 4, 6 of the journey text in `docs/goal.md`), all of which are service actions explicitly blocked this session (pump note: "Do NOT kill, restart, or start any service — the permission classifier blocks it"). Non-disruptive corroboration was still gathered: `GET /api/health` currently returns 200 with `readiness:"ready"`; the persistent logfile `logs/backend.log` exists (41,241 lines) and contains repeated boot-cycle entries (`=== start-backend.sh: launching at <ts> ===`, `Uvicorn running on http://0.0.0.0:8255`, `Application startup complete.`) spanning multiple historical restarts since 2026-07-19, corroborating that the logging half of the journey's infrastructure is intact. This iteration's diff does not touch `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`, or any launch script (binding "Do not redo" per the phase spec's own OUT OF SCOPE section) — this is a pre-existing, unmodified code path, so this SKIP carries no new regression risk from this iteration's actual change. **Operator action needed to fully re-verify J-04 this iteration:** two backend restarts (one immediate-poll, one with the frontend already open) plus one simulated kill, per the journey's literal steps — not performed here.

---

## Notes on this session's operational actions

- Triggered exactly ONE live single-day backfill this session (2025-05-20, run id=150, final message "backfill: 1 snapshots over 1 dates, 2725 forward returns", started 21:53:46 UTC, finished 21:59:49 UTC — ~6m3s), needed to reach the `refreshing` state live per this iteration's own AG-9/AG-10-aware test plan. This is the ONLY ingest job started this QA pass; no other backfills, fetches, or rebuilds were triggered. No service was started, stopped, or restarted at any point (backend pid / frontend remained the ones already running per the pump note throughout).
- Golden replay scripts: none written this run. J-04 (the only additionally-named regression journey) was SKIPPED, not verified PASS, so per the golden-script contract ("for every journey you verify PASS") it does not qualify. J-08 (this iteration's target journey) was verified live for its browser-visible steps 1–3, but step 5 (`not_yet_computed`) was correctly not exercised (see UT-03), so the full journey was not independently verified end-to-end by this agent alone; separately, J-08's interesting behavior (the refreshing window) is inherently tied to a live multi-minute backfill and the replay schema supports only `goto`/`click`/`fill` with no wait/poll primitive, making a fast deterministic replay a poor fit even if the journey had been fully verified. No golden script was fabricated to fill this gap.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-23
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-16-evidence/`
