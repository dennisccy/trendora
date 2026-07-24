# UI Test Results (merged)

**Date:** 2026-07-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 14/15 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-20-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-20-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-20-evidence/J-05-verify.png |
| UT-01 | Latest view loads without errors | smoke | P1 | `/backtest` renders Latest view, "Ready" badge, populated scorecard/cohorts, no errors | URL `/backtest`; heading+subtitle exact match; `readiness-badge`="Ready"/`data-state="ready"`; `asof-trigger`="Latest"; `backtest-asof`="Viewing as-of 2026-07-22 (latest)"; scorecard + Leadership cohorts populated; no console errors | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-01-backtest-latest.png` |
| UT-02 | Never-viewed historical date responds fast + honest interim | happy-path | P1 | Page updates well under 2s; honest Refreshing/EmptyState interim, never a multi-second blank hang | Clicked 2005-07-01 (earliest selectable day, never viewed). `backtest-asof`="Viewing as-of 2005-07-01 (historical)"; `EmptyState` "Backtest evidence not yet computed" rendered essentially immediately (no blank/frozen period observed); browser-measured network duration 1919 ms, backend `total_ms=1321.85` / `ensure_loop_ms=3.34` (see Observations) — an order of magnitude better than the old 9.6-54 s bug | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-02-historical-empty-state.png`, `UT-02-calendar-open.png` |
| UT-03 | Revisit after compute finishes → real ready evidence | happy-path | P1 | Refreshing/EmptyState gone; "Forward-tested evidence" section with real snapshot count | Reloaded `?asof=2005-07-01` after >250 s: `evidence-aggregate` heading "Forward-tested evidence (expanding window ≤ 2005-07-01)"; `evidence-summary`="Snapshots contributing (≤ 2005-07-01): 31"; as-of badge unchanged | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-03-ready-evidence.png` |
| UT-04 | Latest view completely unaffected | regression | P1 | Instant return to Latest, no delay/banner/empty-state, no `?asof=` in URL | Clicked "Latest · 2026-07-22"; URL reverted to `/backtest` (no query param); `backtest-asof`="Viewing as-of 2026-07-22 (latest)"; aggregate section present directly, no refreshing/empty-state; network duration 266 ms | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-04-latest-unaffected.png` |
| UT-05 | RefreshingEvidenceBanner historical copy is true | ux | P2 | Banner names the real historical-dispatch cause, not the ingest/latest-view cause | Clicked 2005-07-15 (fresh date, older-fallback = 2005-07-01). Banner text verified verbatim: no "dataset has changed" / no "after the next ingest finishes"; DOES say "This date's own evidence is being computed in the background (started by viewing this page) and is not complete yet." and "Reload this page shortly to pick up this date's own evidence once the background compute finishes."; names fallback "evidence as of 2005-07-01, generated 2026-07-24 17:32:54"; amber/calm styling, not red | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-05-refreshing-banner.png` |
| UT-06 | EmptyState historical copy is true (best-effort) | ux | P2 | EmptyState credits viewing-the-page as the trigger, not just backfill/fetch | Same 2005-07-01 EmptyState from UT-02 reachable (earliest date, no fallback exists — the narrower "not_yet_computed" condition UT-06 asks for). Exact text: "No forward-tested evidence exists yet for this date. Viewing this page has started computing it in the background — reload shortly to see it." + "No numbers are fabricated in the meantime." — no bare "backfilling or fetching data" phrasing | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-02-historical-empty-state.png` (reused — same observation satisfies both UT-02 and UT-06) |
| UT-07 | Readiness badge never drops during compute | regression | P1 | Badge stays "Ready" throughout the ~30s background compute; nav round-trip completes | `readiness-badge` checked immediately after both cold-date dispatches (2005-07-01, 2005-07-15) and ~15 additional times across the session — always `"Ready"` / `data-state="ready"`, never `"unavailable"`. Dashboard→Backtest round-trip performed during the 2005-07-15 window completed cleanly, badge "Ready" before and after. See Observations for the one caveat (exact 5s-cadence live-window polling not captured; corroborated instead by the operator's own `reports/perf-budgets.md` "Iteration 20" instrumented sampling: 16/16 health samples ready, zero failures) | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-05-refreshing-banner.png` (badge visible top-right), plus inline eval captures in this report |
| UT-08 | Rest of page unaffected during historical first-view | regression | P3 | Every section above the evidence footer renders populated data; only the evidence section shows the interim state | Confirmed twice independently (2005-07-01 EmptyState pass and 2005-07-15 Refreshing pass): Survivorship banner, As-of scan summary, Forward-test scorecard, Return attribution, Leadership cohorts (Top Sectors/Themes/Ranked cohort) all fully populated with real data in both full-page captures; only the bottom evidence-aggregate footer showed the interim state | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-02-historical-empty-state.png`, `UT-05-refreshing-banner.png` |
| UT-09 | Malformed `asof` degrades to Latest | validation | P2 | No crash, URL strips bad param, silently shows Latest | Navigated to `?asof=not-a-real-date`; URL settled to `/backtest` (param stripped); `backtest-asof`="Viewing as-of 2026-07-22 (latest)"; no crash/stack-trace text; only console message was the standard React DevTools info line | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-09-malformed-asof.png` |
| UT-10 | Concurrent second tab slower but never hangs | regression | P3 | Second tab finishes loading (up to ~6s acceptable); never an outright hang/crash | Opened a second tab to `/backtest` (Latest) — loaded cleanly and fast (no live background compute was in flight at that exact moment, see Observations); no hang, no error, no "Backend unavailable" | PASS | Verified via `list_tabs`/`eval` inline (see Observations for the live-contention-timing caveat); operator's own `reports/perf-budgets.md` measurement (3.0-6.3 s under actual contention) is the source for the "slower" half of this claim |
| UT-11 | Backtest + as-of control reachable in 2 clicks | ux | P3 | "Backtest" sidebar link in 1 click; as-of control visible, 2nd click opens calendar | Sidebar list confirmed: Dashboard, Stocks, Themes, Sectors, Scanner Runs, **Backtest**, Research, Evidence, Watchlist, Methodology, Data Manager — matches surface map's "no nav changes"; `asof-trigger` present top-right on `/backtest` (already exercised in UT-02) | PASS | `reports/qa/goal-ops-hardening-iter-20-evidence/UT-11-sidebar-nav.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (goal-mode regression lane) | regression | P1 (Required-still-passing) | Journey's 6 steps executed as a test case | NOT EXECUTED — see "Skipped Tests" below | SKIP | n/a |

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (goal-mode regression lane)

**Verdict:** SKIPPED
**Reason:** NOT EXECUTED — see "Skipped Tests" below

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-24

