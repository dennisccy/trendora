# UI Test Results (merged)

**Date:** 2026-08-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 15/15 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-06-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-11-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-29-evidence/J-07-verify.png |
| UT-01 | Today page loads at 2026-08-03 | smoke | P1 | Heading "Today", subtitle "The ten-second read after the close", badge "Data as-of 2026-08-03", no error card, state band card visible | Heading, subtitle, and badge "Data as-of 2026-08-03" all present; no "Backend unavailable" card; `compass-state-band-card` present in DOM | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-01-result.png` |
| UT-02 | Three badges show real words | happy-path | P1 | Regime="improving", Phase="improving", Breadth="little changed"; none reads "NA" | regime-direction="improving", stress-direction="improving", breadth-direction="little changed" (verified via DOM query on the three data-testids) | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-02-result.png` |
| UT-03 | Regime badge matches Summary sentence | happy-path | P1 | Summary sentence reads exactly "Conditions are improving since the prior session (+4.7 regime-score points)."; "improving" matches Regime badge | `compass-sentence-direction` text = "Conditions are improving since the prior session (+4.7 regime-score points)." — exact match; word "improving" matches Regime tile badge from UT-02 | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-03-result.png` |
| UT-04 | Latest still shows "NA" | regression | P1 | Badge "Data as-of 2026-08-12"; all three direction badges = "NA" | badgeText="Data as-of 2026-08-12", regime="NA", stress="NA", breadth="NA" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-04-result.png` |
| UT-05 | 2025-04-15 still shows "NA" | regression | P2 | Badge "Data as-of 2025-04-15"; all three direction badges = "NA" | badgeText="Data as-of 2025-04-15", regime="NA", stress="NA", breadth="NA" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-05-result.png` |
| UT-06 | Date reachable via calendar click | ux | P2 | Day "3" clickable (not disabled); URL becomes `?asof=2026-08-03`; amber indicator "Viewing as-of 2026-08-03 (historical)"; badges update to improving/improving/little changed | Calendar opened on trigger click, default month showed 2026 / Aug (August 2026); day-3 cell had `data-testid="asof-cal-day"` (not the disabled variant); after click, URL = `/?asof=2026-08-03`, `asof-indicator` text = "Viewing as-of 2026-08-03 (historical)", regime="improving", stress="improving", breadth="little changed" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-06-result.png` |
| UT-07 | Real words survive refresh | regression | P2 | After F5 reload, URL still `?asof=2026-08-03`; badges unchanged | Pre-refresh: regime="improving", stress="improving", breadth="little changed". Post-F5: URL unchanged, same three values unchanged | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-31

