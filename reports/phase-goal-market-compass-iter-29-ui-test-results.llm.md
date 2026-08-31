# Phase goal-market-compass-iter-29 — UI Test Results

**Phase:** goal-market-compass-iter-29
**Date:** 2026-08-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/7 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Today page loads at 2026-08-03 | smoke | P1 | Heading "Today", subtitle "The ten-second read after the close", badge "Data as-of 2026-08-03", no error card, state band card visible | Heading, subtitle, and badge "Data as-of 2026-08-03" all present; no "Backend unavailable" card; `compass-state-band-card` present in DOM | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-01-result.png` |
| UT-02 | Three badges show real words | happy-path | P1 | Regime="improving", Phase="improving", Breadth="little changed"; none reads "NA" | regime-direction="improving", stress-direction="improving", breadth-direction="little changed" (verified via DOM query on the three data-testids) | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-02-result.png` |
| UT-03 | Regime badge matches Summary sentence | happy-path | P1 | Summary sentence reads exactly "Conditions are improving since the prior session (+4.7 regime-score points)."; "improving" matches Regime badge | `compass-sentence-direction` text = "Conditions are improving since the prior session (+4.7 regime-score points)." — exact match; word "improving" matches Regime tile badge from UT-02 | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-03-result.png` |
| UT-04 | Latest still shows "NA" | regression | P1 | Badge "Data as-of 2026-08-12"; all three direction badges = "NA" | badgeText="Data as-of 2026-08-12", regime="NA", stress="NA", breadth="NA" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-04-result.png` |
| UT-05 | 2025-04-15 still shows "NA" | regression | P2 | Badge "Data as-of 2025-04-15"; all three direction badges = "NA" | badgeText="Data as-of 2025-04-15", regime="NA", stress="NA", breadth="NA" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-05-result.png` |
| UT-06 | Date reachable via calendar click | ux | P2 | Day "3" clickable (not disabled); URL becomes `?asof=2026-08-03`; amber indicator "Viewing as-of 2026-08-03 (historical)"; badges update to improving/improving/little changed | Calendar opened on trigger click, default month showed 2026 / Aug (August 2026); day-3 cell had `data-testid="asof-cal-day"` (not the disabled variant); after click, URL = `/?asof=2026-08-03`, `asof-indicator` text = "Viewing as-of 2026-08-03 (historical)", regime="improving", stress="improving", breadth="little changed" | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-06-result.png` |
| UT-07 | Real words survive refresh | regression | P2 | After F5 reload, URL still `?asof=2026-08-03`; badges unchanged | Pre-refresh: regime="improving", stress="improving", breadth="little changed". Post-F5: URL unchanged, same three values unchanged | PASS | `reports/qa/goal-market-compass-iter-29-evidence/UT-07-result.png` |

---

## Passed Tests

### UT-01 — Today page loads at the newly-frozen date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/?asof=2026-08-03`. Heading "Today" and subtitle "The ten-second read after the close" render. Top-right badge reads "Data as-of 2026-08-03" (confirmed via DOM query: `div` with text exactly "Data as-of 2026-08-03"). No "Backend unavailable" text anywhere in the page's extracted markdown. `[data-testid="compass-state-band-card"]` present and non-null.

### UT-02 — All three direction badges render real words, not "NA"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-02-result.png`
- On the same `?asof=2026-08-03` load, queried the three data-testids directly: `compass-state-band-regime-direction` = "improving", `compass-state-band-stress-direction` = "improving", `compass-state-band-breadth-direction` = "little changed". None read "NA".

### UT-03 — Regime badge agrees with the Summary card's direction sentence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-03-result.png`
- `[data-testid="compass-sentence-direction"]` text is exactly "Conditions are improving since the prior session (+4.7 regime-score points)." — matches the spec's expected sentence verbatim. The word "improving" in the sentence matches the Regime tile badge's word from UT-02, confirming no cross-card inconsistency.

### UT-04 — Latest date's state band still shows "NA"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-04-result.png`
- Navigated to `http://localhost:3255/` (no query string). Badge reads "Data as-of 2026-08-12". All three direction badges (regime, stress, breadth) read exactly "NA", confirming the fix is scoped to `2026-08-03` only.

### UT-05 — A second pre-existing safe date also still shows "NA"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-05-result.png`
- Navigated to `http://localhost:3255/?asof=2025-04-15`. Badge reads "Data as-of 2025-04-15". All three direction badges read "NA", unchanged.

### UT-06 — The frozen date is reachable by clicking, not only by typing a URL
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-06-result.png`
- From Latest (`/`), clicked `[data-testid="asof-trigger"]`; the `[data-testid="asof-calendar"]` popover opened with year/month selectors already on 2026 / Aug (August 2026 — screenshot confirms visually) — no month navigation needed. The day cell for "3" (`aria-label="View as-of 2026-08-03"`) had `data-testid="asof-cal-day"` (the enabled variant, not `asof-cal-day-disabled`). After clicking it, the URL became `http://localhost:3255/?asof=2026-08-03`, the `[data-testid="asof-indicator"]` text read "Viewing as-of 2026-08-03 (historical)", and all three direction badges updated to "improving" / "improving" / "little changed".

### UT-07 — The real words survive a page refresh
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-29-evidence/UT-07-result.png`
- Navigated to `?asof=2026-08-03`, confirmed regime="improving", stress="improving", breadth="little changed". Pressed F5 (hard reload confirmed via before/after DOM diff capture). After reload, URL remained `http://localhost:3255/?asof=2026-08-03` and all three direction badges showed the identical values, confirming the row is a persisted database read, not a cached/one-time render.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes

- This iteration's binding constraint (only `{no param (Latest), "2026-08-12" implied, "2025-04-15", "2026-08-03"}` as-of values) was respected throughout — no other `?asof=` value was navigated to, typed, or triggered.
- Console logging was enabled mid-session; no console errors were observed on any page load after enabling.
- Golden replay script updated: `runs/goal-session-market-compass/journey-scripts/J-07.json` — added step 4 (`goto /?asof=2026-08-03`, expect the exact Summary sentence "Conditions are improving since the prior session (+4.7 regime-score points).") to capture this iteration's newly-proven real-words capability, on top of the 3 pre-existing steps for the Latest page. Lint-checked clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-31
- **Evidence directory:** `reports/qa/goal-market-compass-iter-29-evidence/`
