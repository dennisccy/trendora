# UI Test Results (merged)

**Date:** 2026-08-13
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 12/13 journeys passed (1 skipped, 3 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-08-11, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-05-verify.png |
| UT-J-06 | J-06: Pages load only what they need (regression re-confirm) | regression | P1 | All 11 nav pages render real headings/content; the 4 previously-slow endpoints (health/bars/availability/runs) resolve within their combined budgets | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) rendered real headings + substantial DOM. Gated endpoints: `/api/health` 4-15ms; `/stocks/AAPL` bars (cached) 1ms, `chart-window-caption` = "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled" (matches prior baselines byte-for-byte); `/data` `availability-cell`="3", call 25ms; `/scanner-runs` `/api/runs` calls 2372ms/2665ms (elevated — see note below), row visible at 2698ms, still under the 4500ms combined gate | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-06-result.png` |
| UT-J-08 | J-08: Backtest evidence serves from storage only (regression re-confirm) | regression | P1 | `evidence-aggregate`/`evidence-summary` present with real content, "Snapshots contributing" text visible, no blocking/skeleton | At `/backtest` default "Latest" (as-of 2026-08-03, fully-warmed version): `evidence-aggregate` present; `evidence-summary` = "Snapshots contributing (≤ 2026-08-03): 2935 · As-of range: 1999-11-02 → 2026-05-06 · Mean stock fwd return (60d): +3.75% (n=1262535) · Mean max drawdown (60d): -15.49%"; `evidence-refreshing` correctly absent (no pending warm for this version) | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-J-08-result.png` |
| UT-01 | Top bar / preflight banner load cleanly | smoke | P1 | Badge "Ready", preflight "GO — today's board is current." + staleness, no blank/error page | `[data-testid="readiness-badge"][data-state="ready"]` text "Ready"; `[data-testid="preflight-banner"]` text "GO — today's board is current.(as of 0s ago)"; full styled Dashboard rendered, no error boundary | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png` |
| UT-02 | Staleness annotation appears on badge + banner | happy-path | P1 | `readiness-staleness` reads "as of Ns ago" next to pill; same text in parens on preflight strip | `readiness-staleness` = "as of 0s ago"; `preflight-staleness` = "(as of 0s ago)" | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-02-result.png` |
| UT-03 | No annotation on zero-stale / failed poll | validation | P2 | Badge → "Backend unavailable"; `readiness-staleness`/`preflight-staleness` absent; banner → NO-GO w/ "Backend is unavailable" reason; recovers after | With `/api/health` fetches blocked client-side (offline simulation), badge → `data-state="unavailable"` text "Backend unavailable"; both staleness testids absent from DOM; banner = "NO-GO — do not rely on today's board." + "Backend is unavailable — the preflight check could not run."; after restoring fetch, badge recovered to "Ready" with `readiness-staleness`="as of 0s ago" within one poll | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-03-result.png` |
| UT-04 | `/data` honest fallback on fault injection | error | P2 | Red "Backend unavailable" card, exact fallback copy, no coverage numbers | Not exercised this run — see Skipped Tests section | SKIP | none (see note) |
| UT-05 | Ready pill visible alongside compute chip at 1280×800 | regression | P1 | Both badge and `background-compute-indicator` on-screen simultaneously at 1280×800, row wraps rather than clips | At 1280×800 on `/backtest` with 3 dispatched BCWs, `getBoundingClientRect()` confirmed both `readiness-badge` (Ready) and `background-compute-indicator` ("background compute running (3)") fully within the 1280×800 viewport on the same row; "591 symbols" wrapped to a second line | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-05-result.png` |
| UT-06 | Scorecard rows carry `data-testid`, table unchanged | regression | P3 | `scorecard-row-*` count = 5, `scorecard-row-1d` text starts with "1d", table visually unchanged | `document.querySelectorAll('[data-testid^="scorecard-row-"]').length` = 5; ids = 1d/5d/10d/20d/60d; `scorecard-row-1d` text starts "1d"; table renders in its normal Horizon/Cohort/vs SPY/... layout | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-06-result.png` |
| UT-07 | Staleness text is discoverable/clear | ux | P3 | Small muted text next to pill, plainly readable, meaning inferable, parenthesized version reads naturally | "as of 0s ago" renders in small muted-gray text immediately right of the green "Ready" pill (visually distinct, not alarming); "GO — today's board is current.  (as of 0s ago)" reads as one natural sentence | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-01-result.png` (same acceptance state as UT-01/02) |
| UT-08 | NO-GO banner still names reasons, no stale annotation | regression | P2 | Banner reads exact NO-GO phrase + reason bullet; no staleness annotation; recovers to GO | Same blocked-poll window as UT-03: banner = "NO-GO — do not rely on today's board." with bullet "Backend is unavailable — the preflight check could not run."; `preflight-staleness` absent; after restore, banner returned to "GO — today's board is current. (as of 0s ago)" | PASS | `reports/qa/goal-ops-hardening-iter-77-evidence/UT-08-result.png` |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-04` — no test case executed for J-04 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane
- `UT-J-09` — no test case executed for J-09 by any lane

## Skipped Tests

### UT-04 — `/data` honest fallback on fault injection

**Verdict:** SKIPPED
**Reason:** Not exercised this run — see Skipped Tests section

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-13

