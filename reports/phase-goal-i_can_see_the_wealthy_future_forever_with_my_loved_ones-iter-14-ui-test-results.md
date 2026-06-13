# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 — UI Test Results

**Browser QA Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3835
**Backend URL:** http://localhost:8835
**Browser:** Chrome (via Chrome MCP)

---

## Summary

**16/16 tests passed** (9 P1 smoke/happy-path/regression + 7 P2 validation/ux)

All P1 tests passed. All P2 tests passed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | /research loads with Episodes toggle visible | smoke | P1 | Episodes toggle visible and active | Episodes button aria-pressed=true (bg-accent, font-semibold); Pooled aria-pressed=false | PASS | UT-01-result.png |
| UT-02 | /methodology loads with Episode and Pooled entries | smoke | P1 | Both glossary entries present with definitions | "Episode" entry with first-trigger definition; "Pooled (per-signal-day)" entry with per-signal-day definition; neither duplicated | PASS | UT-02-result.png |
| UT-03 | /research/samples loads with cohort detail line | smoke | P1 | Cohort header line visible on /research/samples | "Slice: Episodes (first-trigger) · All occurrences", "Total observations: 106" visible in header | PASS | UT-03-result.png |
| UT-04 | Toggling Episodes to Pooled updates pill and n | happy-path | P1 | n changes, Pooled becomes active, in-place update | Episodes n=106 → Pooled n=180 (signal-days); toggle switches aria-pressed bidirectionally; history length unchanged (no page reload) | PASS | UT-04-before.png, UT-04-pooled.png |
| UT-05 | Disclosure line shows n, Unique symbols, Episodes | happy-path | P1 | All 3 values visible and non-zero | "n (20d, episodes): 106 / Unique symbols: 48 / Episodes: 106" — all three present and non-zero | PASS | UT-05-result.png |
| UT-06 | N= chip in Episodes mode links with view=episodes | happy-path | P1 | URL has view=episodes | All event-study n= links contain view=episodes (e.g. /research/samples?kind=event-study&horizon=1&subject=Actionable&slice=pooled&view=episodes) | PASS | UT-06-episodes-chips.png |
| UT-07 | N= chip in Pooled mode links with view=pooled | happy-path | P1 | URL has view=pooled, n larger than episodes | In Pooled mode all links switch to view=pooled; n=181 (larger than episodes n=107); zero view=episodes links remain | PASS | UT-04-pooled.png |
| UT-08 | Samples drill-down from Episodes chip shows "Episodes (first-trigger)" | happy-path | P1 | Cohort label "Episodes (first-trigger)" visible | "Slice: Episodes (first-trigger) · All occurrences" visible; Total observations: 106 matches N= chip | PASS | UT-08-result.png |
| UT-09 | Samples drill-down from Pooled chip shows "Pooled (per-signal-day)" | happy-path | P1 | Cohort label "Pooled (per-signal-day)" visible | "Slice: Pooled (per-signal-day) · All occurrences" visible; Total observations: 180 > 106 (episodes) | PASS | UT-09-result.png |
| UT-10 | Disclosure line tooltip on Episode term click | validation | P2 | Tooltip with Episode definition appears | button[aria-label="Definition of Episode"] found; clicking sets aria-expanded=true; popover appears with Episode definition text; URL unchanged | PASS | UT-10-tooltip.png |
| UT-11 | Toggling view does not change as-of date or URL | validation | P2 | URL unchanged after toggling, no history entries added | URL stayed http://localhost:3835/research throughout; history.length=2 before and after both toggles | PASS | — |
| UT-12 | Event study figures present in both Episodes and Pooled modes | regression | P1 | All figures (hit-rate, expectancy, MAE, MFE, by-regime, by-sector) in both modes | All six figure types confirmed present in Episodes (n=106) and Pooled (n=180) modes; numeric values differ between modes | PASS | UT-12-pooled-figures.png |
| UT-13 | /research/samples sort/filter controls still work | regression | P1 | Sort changes row order, total unchanged | Sort buttons present (Latest, Ticker, Snapshot date, Matched, Forward return); clicking "Ticker" reordered rows from COST/WMT/ZS/TXN → AAPL/COST/DELL/DELL; Total observations remained 106 | PASS | UT-13-sorted.png |
| UT-14 | Episode and Pooled glossary entries complete on /methodology | regression | P2 | Both entries have distinct, authored definitions | Episode entry: full first-trigger definition; Pooled entry: full per-signal-day definition; each appears exactly once; definitions are distinct | PASS | UT-14-glossary.png |
| UT-15 | Episodes mode is default on fresh page load | ux | P2 | Episodes active on fresh load, n is lower episode count | Fresh navigation to /research: Episodes aria-pressed=true, Pooled aria-pressed=false, disclosure shows "n (20d, episodes): 106" | PASS | — |
| UT-16 | Episodes/Pooled toggle visually distinct and labelled clearly | ux | P2 | Toggle visible, active state visually distinct | Toggle in viewport (top=444px); Episodes has bg-accent + font-semibold; Pooled has text-text-muted + hover styles only; labels are plain text | PASS | UT-16-toggle.png |

---

## Failure Details

None — all 16 tests passed.

---

## Environment

- Frontend URL: http://localhost:3835
- Backend URL: http://localhost:8835 (health: /api/health returns status=ok, seed 2026-05-28, 159 symbols)
- Browser: Chrome (via Chrome MCP / mcp__plugin_superpowers-chrome_chrome__use_browser)
- Date: 2026-06-13
- Evidence directory: reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14-evidence/
