# UI Test Results (merged)

**Date:** 2026-07-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/16 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-13-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-13-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-13-evidence/J-05-verify.png |
| UT-01 | Dashboard loads without errors | smoke | P1 | Page renders, cards resolve to data, no console errors | Fresh nav to `/`: "Regime × phase cross-view" card (the live home of the historical "Major indexes & regime" content — see note) rendered with all 10 index lines + regime bands; no console errors; no skeleton stuck | PASS | `UT-01-result.png` |
| UT-02 | Data Manager loads without errors | smoke | P1 | `index-vendor-panel` + job-form card visible, resolves within seconds, no console errors | Fresh nav to `/data`: vendor panel populated (10 rows), job-form card visible, no `index-vendor-loading` skeleton stuck, no console errors | PASS | `UT-02-result.png` |
| UT-03 | Hot-key latency ≤1.5s, 3 fresh `/data` loads (canonical J-06 measurement) | happy-path | P1 | 3 fresh-nav `GET /api/indexes?full=true` readings ≤1500ms, host idle, content unchanged | Readings: 218.7ms / 218.7ms / 219.2ms — all ≤1500ms with ~7x margin; `load1` 0.36–0.69 all three times; vendor table byte-identical across all three loads | PASS | `UT-03-load1-result.png`, `UT-03-reading3.png` |
| UT-04 | Hot-key latency ≤1.5s, `/` spot-check | happy-path | P1 | 1 fresh-nav reading ≤1500ms, chart renders | Reading: 70.5ms (single entry, no StrictMode double-fire — abort guard present); `load1` 0.36–0.54; chart + tooltip both populated, as-of `2026-07-17` shown | PASS | `UT-04-result.png` |
| UT-05 | Vendor panel content unchanged | regression | P1 | Every configured symbol shows a named vendor or honest "—", no blanks | All 10 rows present (SPY/QQQ/IWM/RSP/DIA → "—"; ^SPX/^NDX/^DJI → Stooq; ^VIX → Yahoo; ^TNX → FRED-macro proxy), every first-bar date populated, no blank/undefined cell, no "Vendor disclosure unavailable" warning | PASS | `UT-02-result.png` (same panel read) |
| UT-06 | Dashboard chart content unchanged | regression | P2 | As-of date current, tooltip populated, both panes consistent | As-of `2026-07-17` shown (current trading day at test time); hover tooltip at `2025-08-15` showed all 10 index %, regime `Risk-on · 72/100`, phase `Expansion`, severity `26`, P(bear) `0.00` — fully populated, no "N/A" | PASS | `UT-06-tooltip-populated.png` |
| UT-07 | Non-default range preset still works | regression | P1 | `aria-label="Range preset"` dropdown selects "3M", chart re-renders shorter window | **Element does not exist on the live page** — `document.querySelectorAll('[aria-label="Range preset"]')` returned 0 matches; confirmed via source grep that the owning component (`major-indexes-card.tsx`) is dead code, unreachable from any route (0 imports outside its own file). See "Read this first" section for full analysis — not a regression from this iteration; underlying backend behavior independently confirmed via real-browser `fetch()` (200, 661ms, 10 series) | **FAIL** | none (element absent) |
| UT-08 | "index series" appears in Refreshed line | happy-path | P2 | New job's Refreshed line includes "index series" when gated | Could not reproduce live this session — my own diagnostic API read self-healed the cache before the ingest job's own turn (see "UT-08/09/10" section); positive path is unit-tested (`test_data_manager.py -k index_series`, 30 passed per dev handoff) but not exercised end-to-end via the live UI | SKIP (not exercised) | `UT-08-form-filled.png`, `UT-08-job-running.png` |
| UT-09 | "index series" honestly omitted elsewhere | regression | P2 | A row with it present + a row without it, both correct | Could not get a "present" row this session (see above); confirmed 0 of 41 visible Run History `Refreshed:` rows fabricate "index series" — the honest-omission gate held on every observed row, including a run whose date range genuinely landed new index-symbol bars | SKIP (partial evidence — omission confirmed broadly, positive-row comparison not possible) | DOM read (see report body); `UT-09-run-history.png`/`-viewport.png` are blank (see technique note) |
| UT-10 | Refreshed line reads clearly | ux | P3 | Plain-English list, "index series" styled identically to other items | No live instance of the string "index series" was available to inspect this session (see UT-08) | SKIP (not exercised) | none |
| UT-11 | Vendor-panel error state unchanged | error | P3 | "Vendor disclosure unavailable" wording on backend-down | No natural backend-down window occurred; I did not force one (services in this session are restarted only by the operator, per this iteration's pump note and explicit dispatch instruction) | SKIP (not exercised) | none |
| UT-12 | `/evidence` spot-check, no regression | regression | P2 | Within committed 3s budget, no console errors | `domContentLoaded` 581ms, `loadEvent` 761ms, `GET /api/evidence` 27ms — all well within the `≤3s` committed budget (`reports/perf-budgets.md`); no console errors | PASS | `UT-12-evidence-page.png` |
| UT-J-04 | Non-blocking boot with visible status (regression journey, dispatch-required) | regression | P1 | Restart→≤5s first-200, phase-aware badge, crash→honest-unreachable, log evidence, interrupted-job recovery | **Could not be exercised** — 5 of J-04's 6 steps require a live backend restart or kill, which I am explicitly instructed not to perform myself this run. See "J-04" section below for exactly what I could and could not confirm, and the exact operator action needed. | SKIP | none |

## Skipped Tests

### UT-J-04 — Non-blocking boot with visible status (regression journey, dispatch-required)

**Verdict:** SKIPPED
**Reason:** **Could not be exercised** — 5 of J-04's 6 steps require a live backend restart or kill, which I am explicitly instructed not to perform myself this run. See "J-04" section below for exactly what I could and could not confirm, and the exact operator action needed.

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-23

