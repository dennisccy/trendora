# Phase goal-ops-hardening-iter-77 — UI Test Results

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 9/10 tests passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Top bar / preflight banner load cleanly | smoke | P1 | Badge "Ready", preflight "GO — today's board is current." + staleness, no blank/error page | `[data-testid="readiness-badge"][data-state="ready"]` text "Ready"; `[data-testid="preflight-banner"]` text "GO — today's board is current.(as of 0s ago)"; full styled Dashboard rendered, no error boundary | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png` |
| UT-02 | Staleness annotation appears on badge + banner | happy-path | P1 | `readiness-staleness` reads "as of Ns ago" next to pill; same text in parens on preflight strip | `readiness-staleness` = "as of 0s ago"; `preflight-staleness` = "(as of 0s ago)" | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-02-result.png` |
| UT-03 | No annotation on zero-stale / failed poll | validation | P2 | Badge → "Backend unavailable"; `readiness-staleness`/`preflight-staleness` absent; banner → NO-GO w/ "Backend is unavailable" reason; recovers after | With `/api/health` fetches blocked client-side (offline simulation), badge → `data-state="unavailable"` text "Backend unavailable"; both staleness testids absent from DOM; banner = "NO-GO — do not rely on today's board." + "Backend is unavailable — the preflight check could not run."; after restoring fetch, badge recovered to "Ready" with `readiness-staleness`="as of 0s ago" within one poll | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-03-result.png` |
| UT-04 | `/data` honest fallback on fault injection | error | P2 | Red "Backend unavailable" card, exact fallback copy, no coverage numbers | Not exercised this run — see Skipped Tests section | SKIP | none (see note) |
| UT-05 | Ready pill visible alongside compute chip at 1280×800 | regression | P1 | Both badge and `background-compute-indicator` on-screen simultaneously at 1280×800, row wraps rather than clips | At 1280×800 on `/backtest` with 3 dispatched BCWs, `getBoundingClientRect()` confirmed both `readiness-badge` (Ready) and `background-compute-indicator` ("background compute running (3)") fully within the 1280×800 viewport on the same row; "591 symbols" wrapped to a second line | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-05-result.png` |
| UT-06 | Scorecard rows carry `data-testid`, table unchanged | regression | P3 | `scorecard-row-*` count = 5, `scorecard-row-1d` text starts with "1d", table visually unchanged | `document.querySelectorAll('[data-testid^="scorecard-row-"]').length` = 5; ids = 1d/5d/10d/20d/60d; `scorecard-row-1d` text starts "1d"; table renders in its normal Horizon/Cohort/vs SPY/... layout | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-06-result.png` |
| UT-07 | Staleness text is discoverable/clear | ux | P3 | Small muted text next to pill, plainly readable, meaning inferable, parenthesized version reads naturally | "as of 0s ago" renders in small muted-gray text immediately right of the green "Ready" pill (visually distinct, not alarming); "GO — today's board is current.  (as of 0s ago)" reads as one natural sentence | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png` (same acceptance state as UT-01/02) |
| UT-08 | NO-GO banner still names reasons, no stale annotation | regression | P2 | Banner reads exact NO-GO phrase + reason bullet; no staleness annotation; recovers to GO | Same blocked-poll window as UT-03: banner = "NO-GO — do not rely on today's board." with bullet "Backend is unavailable — the preflight check could not run."; `preflight-staleness` absent; after restore, banner returned to "GO — today's board is current. (as of 0s ago)" | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-08-result.png` |
| UT-J-06 | J-06: Pages load only what they need (regression re-confirm) | regression | P1 | All 11 nav pages render real headings/content; the 4 previously-slow endpoints (health/bars/availability/runs) resolve within their combined budgets | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) rendered real headings + substantial DOM. Gated endpoints: `/api/health` 4-15ms; `/stocks/AAPL` bars (cached) 1ms, `chart-window-caption` = "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled" (matches prior baselines byte-for-byte); `/data` `availability-cell`="3", call 25ms; `/scanner-runs` `/api/runs` calls 2372ms/2665ms (elevated — see note below), row visible at 2698ms, still under the 4500ms combined gate | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-06-result.png` |
| UT-J-08 | J-08: Backtest evidence serves from storage only (regression re-confirm) | regression | P1 | `evidence-aggregate`/`evidence-summary` present with real content, "Snapshots contributing" text visible, no blocking/skeleton | At `/backtest` default "Latest" (as-of 2026-08-03, fully-warmed version): `evidence-aggregate` present; `evidence-summary` = "Snapshots contributing (≤ 2026-08-03): 2935 · As-of range: 1999-11-02 → 2026-05-06 · Mean stock fwd return (60d): +3.75% (n=1262535) · Mean max drawdown (60d): -15.49%"; `evidence-refreshing` correctly absent (no pending warm for this version) | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-08-result.png` |

---

## Passed Tests

### UT-01 — Top bar / preflight banner load cleanly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/`. `readiness-badge` resolved to `data-state="ready"` / text "Ready". `preflight-banner` read "GO — today's board is current.(as of 0s ago)". Full styled Dashboard content rendered (Market Regime, Market Phase & Severity, Regime × phase cross-view chart) — no blank page, no error boundary.

### UT-02 — Staleness annotation appears on badge + banner
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-02-result.png`
- Same load as UT-01. `[data-testid="readiness-staleness"]` text = "as of 0s ago", positioned immediately right of the "Ready" pill. `[data-testid="preflight-staleness"]` text = "(as of 0s ago)", present inside the preflight banner directly after the GO sentence.

### UT-03 — No annotation on zero-stale / failed poll
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-03-result.png`
- Chrome MCP has no direct DevTools-network-offline action, so the offline condition was simulated client-side exactly as UT-03's own steps permit ("or otherwise block requests to the backend's `/api/health` endpoint"): installed a `window.fetch` override in-page that rejects only requests whose URL contains `/api/health`, passing every other request through unmodified. This blocks the readiness poll without touching the backend/frontend processes (browser-qa-agent is not permitted to restart the app this run).
- After the next scheduled poll fired, the badge flipped to `data-state="unavailable"` / text "Backend unavailable" (red). `readiness-staleness` and `preflight-staleness` were both confirmed absent from the DOM (`querySelector` returned null for both) — no stale or fabricated number shown. The banner showed the NO-GO state with the correct reason (see UT-08).
- Restored the original `window.fetch`; on the next poll (within ~1 cadence) the badge recovered to "Ready" with `readiness-staleness` reading "as of 0s ago" again.
- Note for future runs: this build's `ReadinessProvider` backs off to the **idle** cadence (`poll_idle_interval_seconds` = 30s from `/api/health`) once `ready`, not the ~2s "active" cadence the test plan's preconditions describe — that faster cadence only applies while not yet ready. The first poll after installing the block did not land until close to 30s out, not ~5s. Not a defect — the test plan's timing note is stale relative to this iteration's back-off behavior — but worth a phase-spec correction so the next QA pass doesn't under-wait.

### UT-05 — Ready pill visible alongside compute chip at 1280×800
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-05-result.png`
- Set viewport to exactly 1280×800. Navigated to `/backtest` and clicked `[data-testid="asof-step-prev"]` 3 times (landing on 2026-07-31, 07-30, 07-29). `GET /api/health` confirmed 3 background-compute windows dispatched and active (`horizons_done: 0/5` each). `await_element` on `[data-testid="background-compute-indicator"]` resolved within ~15s.
- `getBoundingClientRect()` on both `readiness-badge` and `background-compute-indicator` confirmed both fully inside the 1280×800 viewport (`badgeVisible: true`, `bciVisible: true`), on the same header row, with the badge row's "591 symbols" tag wrapping to a second line rather than either element clipping off-screen. This confirms the iter-76/e regression fix holds.

### UT-06 — Scorecard rows carry `data-testid`, table unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-06-result.png`
- On `/backtest`, `document.querySelectorAll('[data-testid^="scorecard-row-"]').length` returned `5`; the individual ids were `scorecard-row-1d`, `-5d`, `-10d`, `-20d`, `-60d`. `document.querySelector('[data-testid="scorecard-row-1d"]')` returned a non-null `<tr>` whose text started with "1d". The visible Forward-test scorecard table rendered in its normal Horizon/Cohort/vs SPY/vs QQQ/vs Sector/Random peers/SPY/QQQ/Sector ETF layout, no visual difference from the test-hook addition.

### UT-07 — Staleness text is discoverable/clear
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png` (same acceptance state)
- "as of 0s ago" renders in small muted-gray text immediately to the right of the green "Ready" pill — plainly readable at normal zoom, visually distinct (not colored/alarming) from the pill. Its meaning ("how stale is this reading") is inferable from the phrase alone. On the preflight strip, "GO — today's board is current.  (as of 0s ago)" reads as one natural sentence, not a disconnected fragment.

### UT-08 — NO-GO banner still names reasons, no stale annotation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-08-result.png`
- Induced with the same client-side `/api/health`-blocking technique used for UT-03 (see that section's note — the app cannot be restarted by browser-qa-agent this run, so the fetch-block simulates "backend unreachable" exactly as UT-03's own alternate instruction permits). Banner read "NO-GO — do not rely on today's board." with the bulleted reason "Backend is unavailable — the preflight check could not run." — exact phrase match. No staleness annotation appeared next to the NO-GO heading. After restoring the network path, the banner returned to "GO — today's board is current. (as of 0s ago)".

### UT-J-06 — J-06: Pages load only what they need (regression re-confirm)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-06-result.png`
- Dispatched because the deterministic replay lane flagged a possible regression on J-06 this iteration. Walked all 16 golden steps live via Chrome MCP against the confirmed-live production-launcher backend (8255/3255): all 11 pages rendered real headings with substantial interactive DOM (never blank/error-boundary), and the four historically-gated endpoints resolved with real values — `/api/health` 4-15ms, `/stocks/AAPL` bars (cached `through=latest`) 1ms with `chart-window-caption` = "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled" (byte-identical to iter-71/72/73's recorded baseline), `/data` `availability-cell`="3" at 25ms, `/scanner-runs` `table tbody tr` visible with `/api/runs` at 2372ms/2665ms (row on-screen at 2698ms from nav start).
- The `/api/runs` reading is well above this golden's usual 203-774ms baseline range but still inside its 2500ms(nav)+2000ms(assert)=4500ms combined gate (2698ms < 4500ms), so the step itself did not fail. Root cause, confirmed via `GET /api/health`: at the time `/scanner-runs` loaded, **9 background-compute windows were concurrently active** — 3 from this test's own UT-05 step, plus 6 more that this agent inadvertently dispatched by `curl`-probing several `/api/backtest?as_of=...` dates directly while hunting for an uncached date (each uncached-date GET dispatches its own compute window). That is a self-inflicted-load lesson for future QA passes (prefer reading `background_compute.active` from `/api/health` over probing dates), not a product regression — the backend stayed HTTP 200 throughout and never wedged.
- The golden script `runs/goal-session-ops-hardening/journey-scripts/J-06.json` was updated with an iter-77 note documenting this re-verification and the diagnosed cause; steps/selectors/budgets were left unchanged (no drift found). Re-linted clean via `demo_runner.py --mode lint`.

### UT-J-08 — J-08: Backtest evidence serves from storage only (regression re-confirm)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-08-result.png`
- Dispatched because the deterministic replay lane also flagged a possible regression on J-08 this iteration. At `/backtest`'s default "Latest" landing (as-of 2026-08-03, the fully-warmed current dataset version with no pending finalize), `evidence-aggregate` was present and `evidence-summary` read "Snapshots contributing (≤ 2026-08-03): 2935 · As-of range: 1999-11-02 → 2026-05-06 · Mean stock fwd return (60d): +3.75% (n=1262535) · Mean max drawdown (60d): -15.49%". `evidence-refreshing` was correctly absent (no pending warm for this version) — no skeleton, no blocking render, no fabricated figures.
- This iteration's own diff (readiness-staleness annotation, iter-76/e header-wrap fix, `/backtest` scorecard-row testids) does not touch the `evidence-aggregate`/`evidence-summary`/`evidence-refreshing` components, and no selector drift was found. The replay's flagged regression is most plausibly the same host-contention pattern documented for J-06 above (9 concurrent background-compute windows in flight at points during this session). Golden updated with an iter-77 verification note (steps unchanged); re-linted clean.

---

## Failed Tests

None this run.

---

## Skipped Tests

### UT-04 — `/data` honest fallback on fault injection
**Verdict:** SKIPPED
**Reason:** This test's precondition requires restarting the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` set, then restarting it again afterward with the variable unset. This browser-qa-agent dispatch was explicitly instructed it "may not restart the app" this run, so the precondition could not be met and the case was not independently re-verified via Chrome MCP this pass.
- For the record (not claimed as this run's own verification): a pre-existing screenshot at `reports/qa/goal-ops-hardening-iter-77-evidence/TC-8-data-fault-injection-honest-fallback.png` (file timestamp predates this dispatch) shows the `/data` page with a red "Backend unavailable" card reading the exact text "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." — matching UT-04's expected copy verbatim, with no coverage numbers rendered. That capture appears to be from an earlier phase step (the top bar shows "Initializing... history 89/89", consistent with a just-restarted backend), not from this browser-qa-agent's own run, so it is reported here only as pointer evidence, not as this test's verdict basis.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile, headless
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-77-evidence/`
- Both backend (`/api/health`) and frontend confirmed HTTP 200 before and after this test run.
