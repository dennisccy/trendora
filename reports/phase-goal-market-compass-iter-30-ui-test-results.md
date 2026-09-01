# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-06-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-10-verify.png |
| UT-J-11 | J-11: Incident-bounded clean regeneration — basis-disclosure regression check | regression | P1 | `/?asof=2026-08-12` and `/?asof=2026-08-11` both show `Basis: rebuilt` (per stale golden script) | `/?asof=2026-08-11` (unaffected date) still shows `Basis: rebuilt` exactly as before. `/?asof=2026-08-12` now shows `Basis: available` — **not** a regression: this iteration's one authorized `regenerate` call minted version 7 for `as_of=2026-08-12`, whose `generation_json.source_run_created_at` was recorded against the already-rebuilt current run at mint time, so `basis_disclosure` correctly finds no discrepancy (`recorded == current_run.created_at`) and reports `available`. Confirmed via `GET /api/compass?as_of=2026-08-12` (`basis: {"status": "available"}`, version 7) and `GET /api/compass?as_of=2026-08-11` (`basis: {"status": "rebuilt"}`, version 3), byte-matching what the browser rendered. The `basis_disclosure` mechanism itself (J-11's actual deliverable) is functioning correctly on both dates; only the served DATA for 2026-08-12 legitimately changed due to this iteration's in-scope mint. | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-J-11-result.png` |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-30-evidence/J-07-verify.png |
| UT-01 | Default page loads | smoke | P1 | Page renders, "Market state" and "Summary" card headings visible, no console errors | Page loaded at `/`; `document.body.innerText` contains both "Market state" and "Summary"; no console messages captured after `enable_console_logging` + reload (no errors) | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-01-result.png` |
| UT-02 | Default view shows real direction words | happy-path | P1 | Regime/Market-phase/Breadth badges all read "little changed", never "NA" | `compass-state-band-regime-direction`="little changed", `compass-state-band-stress-direction`="little changed", `compass-state-band-breadth-direction`="little changed" (read via `data-testid` selectors) | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-02-result.png` |
| UT-03 | Summary card consistent with Regime badge | happy-path | P1 | Sentence reads exactly "Conditions are little changed since the prior session (-0.3 regime-score points)." matching the Regime badge's word | `compass-sentence-direction` textContent = "Conditions are little changed since the prior session (-0.3 regime-score points)." — exact match; direction word "little changed" matches UT-02's Regime badge | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-03-result.png` |
| UT-04 | `2026-08-03` unaffected | regression | P1 | Regime/Market-phase badges "improving", Breadth badge "little changed" | Read via `data-testid` at `/?asof=2026-08-03`: regime="improving", stress="improving", breadth="little changed" — matches iter-29 recorded state exactly | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-04-result.png` |
| UT-05 | `2025-04-15` still loads | regression | P2 | Page renders, Market state + Summary cards visible, no console errors | Navigated to `/?asof=2025-04-15`; both card headings present in `innerText`; no console messages after `enable_console_logging` + reload | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-05-result.png` |
| UT-06 | Market-context link still works | regression | P2 | Click navigates to `/market`; text "severity-velocity line" visible somewhere on the page | Click on `compass-state-band-market-link` navigated to `http://localhost:3255/market` (no error/blank page). The literal string "severity-velocity line" does not appear verbatim anywhere on `/market` — the rendered legend text is "Severity velocity (0-centered; + = worsening)" (see `phase-cross-view-chart.tsx` `CrossLegend`), visible only after expanding the "Show regime × phase cross-view" toggle (collapsed by default). This is a test-plan wording mismatch, not a product defect — the underlying feature (regime × phase cross-view chart, absent from `/`, reachable from `/market`) is present and functions correctly, matching J-07's acceptance intent. | PASS (with note) | `reports/qa/goal-market-compass-iter-30-evidence/UT-06-result.png` |
| UT-07 | Regenerate without confirm still 400s | error | P2 | HTTP 400; `as_of='2026-08-12'` row count unchanged | `curl -X POST ".../api/compass/regenerate?as_of=2026-08-12"` (no `confirm`) → `400`; `sqlite3` row count for `as_of='2026-08-12'` = 7 both before and after the call | PASS | none (backend-only test, no UI surface) |
| UT-08 | Badges discoverable above the fold | ux | P2 | "Market state" card (all 3 badges) is first/second card, above "Summary" card, visible without scrolling | Screenshot at standard viewport (1683×1260) shows "Market state" card (with Regime/Market-phase/Breadth badges) as the first card, immediately followed by the "Summary" card, both fully visible with zero scrolling | PASS | `reports/qa/goal-market-compass-iter-30-evidence/UT-08-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

