# Phase goal-mcp-loop-iter-41 — UI Test Results

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/14 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page loads, panel present on all 7 cards | smoke | P1 | 7 claim cards, each with an expectations panel + table; no empty state; no backend error | `evidence-claim-row`=7, `evidence-expectations-panel`=7, `evidence-expectations-table`=7, `evidence-empty`=0, no "Backend unavailable" text, h1="Evidence", `/api/evidence` warm latency ~5ms | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` |
| UT-02 | Read real Expansion-row figures (card 1) | happy-path | P1 | Exact heading + exact Expansion-row cell values + method note/caveat wording; no forecast/promise language | Heading, Max-DD, Underwater, Time-to-recover cells byte-matched exactly; method note + survivorship caveat byte-matched exactly; no promise words found (see note) | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` |
| UT-03 | Below-floor streak insufficient, siblings real | validation | P2 | Correction row: streak cell "insufficient (n=5)" muted; other 3 cells show real values | Streak cell = `insufficient (n=5)` in a `text-text-faint` span; Max-DD/Underwater/Time-to-recover cells all real, non-blank values | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` |
| UT-04 | Zero-observation cohort insufficient(n=0) | error | P2 | Card 2 Correction + Bear rows: all 4 measure cells "insufficient (n=0)"; no crash; other rows normal | Both rows: all 4 cells exactly `insufficient (n=0)`; Expansion/Pullback/Recovery rows on same card show real values; card header/badges intact | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-04-card2-zero-obs.png` |
| UT-05 | Absent-panel contract check (best-effort) | error | P3 | Every claim object in `GET /api/evidence` has non-null `expectations`; every card shows the panel | All 7 claim objects have populated `expectations` with keys `by_phase`/`horizon`/`method_note`/`min_sample`/`streak_min_n`/`survivorship_bias` and 5 phases in order; all 7 cards render the panel (0 missing) | PASS | verified via direct `GET /api/evidence` fetch (see note) |
| UT-06 | Existing field grid / verdict badges unchanged | regression | P1 | 5 field labels in exact order on all 7 cards; all verdicts FAIL; panel strictly below grid; no stale values | Field labels exact-match on all 7/7 cards; all 7 verdict badges = "FAIL"; panel appears exactly once per card, always after the `<dl>`; zero hits for "+21.34%", "+6.36%", "p=0.0004998" | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` |
| UT-07 | Regime badge still correct | regression | P1 | Card 2 shows a legible "Regime: Risk-on" badge next to FAIL | `evidence-claim-regime` = "Regime: Risk-on", present and legible; dashboard cross-check phase = "Expansion" (informational only, legitimately different scope) | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-04-card2-zero-obs.png` |
| UT-08 | GO preflight strip unaffected | regression | P1 | Thin strip visible with GO/DEGRADED/NO-GO text, not overlapped | `preflight-banner` text = "GO — today's board is current.", not cut off/overlapped | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` |
| UT-09 | Stock deep-history chart controls | regression | P1 | Heading "AAPL"; Recent/Full history buttons present; clicking Full history loads deeper history | h1="AAPL"; both buttons present; click toggled `aria-pressed` Recent→Full; bar count 1255→3185 with "older bars weekly-sampled" appended (see note on "history since" wording) | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-09-before-click.png`, `UT-09-after-full-history.png` |
| UT-10 | Data Manager page loads | regression | P1 | Heading "Data Manager"; subtitle starts "Grow the dataset on demand"; Dataset coverage panel; no blank/error | All confirmed exactly; no blank page, no error | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-10-data-manager.png` |
| UT-11 | Proven / Not yet proven badges | regression | P1 | All score badges on `/stocks` and `/stocks/AAPL` read "Not yet proven"; tooltip present | 1623/1623 badges on `/stocks` = "Not yet proven" (0 "Proven"); 3/3 on AAPL = "Not yet proven"; tooltip title = "Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)." | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-11-stocks-leaderboard.png`, `UT-11-UT-12-aapl-scores.png` |
| UT-12 | Score-drill honest absence | regression | P1 | No "Why proven?" toggle on any of the 3 AAPL score cards | `score-proof-toggle` count = 0 on `/stocks/AAPL`; no broken/empty box in its place | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-11-UT-12-aapl-scores.png` |
| UT-13 | Caveat visible + consistent wording | ux | P3 | Method note + survivorship caveat visible without interaction; identical wording across cards | Both elements `display:block`/`visibility:visible`/no max-height clamp; card 1 and card 3 text byte-identical | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-13-UT-14-card1-panel.png` |
| UT-14 | Phase-badge color gap (known minor) | ux | P3 | New table's phase badges all flat gray regardless of phase name; dashboard badge is color-coded (known, tracked gap) | All 5 phase badges (Expansion/Pullback/Correction/Bear/Recovery) share the identical class `border-border bg-surface-2 text-text-muted` — confirmed flat neutral, no color differentiation, matching the documented gap | PASS | `reports/qa/goal-mcp-loop-iter-41-evidence/UT-13-UT-14-card1-panel.png` |

---

## Passed Tests

### UT-01 — Page loads, panel present on all 7 cards
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png` (full-page)
- Navigated to `/evidence`, waited for the client fetch to resolve ("Historical drawdown" text awaited before asserting, per the coordinator's note that the panel is client-rendered).
- DOM query: `evidence-claim-row`=7, `evidence-expectations-panel`=7, `evidence-expectations-table`=7, `evidence-empty`=0, `Backend unavailable` text absent, `h1`="Evidence".
- `GET /api/evidence` measured at ~5ms warm latency (two consecutive curls: 0.00516s, 0.00472s) — well under 1 second, consistent with `reports/perf-budgets.md`'s recorded warm-cache figure.

### UT-02 — Read real Expansion-row figures (card 1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png`
- Card 1 Hypothesis chips confirmed `factor=leadership_score`/`decile=10`/`horizon=20` (visible in screenshot).
- Panel heading DOM text: exactly `"Historical drawdown & dry-spell expectations (20-day hold)"`.
- Expansion row cells (exact `textContent`): Max-DD depth = `"-7.70% (p90 -3.72%) n=1264"`, Underwater = `"20.0d (p90 20.0d) n=1264"`, Time to recover = `"0.0d (p90 6.0d) n=769"` — all three byte-match the test plan's expected strings exactly.
- Method note starts `"Longest losing streak is counted at the walk-forward cadence"`; survivorship sentence starts `"Walk-forward evidence now spans up to ~30 years of history"` and ends `"Read the edge as an upper bound, not a guarantee."` — both byte-match.
- **Note on forbidden-word scan:** a page-wide scan for `expect to/forecast/predict/target/buy/sell/trim/reduce/you will` found one substring hit — `"forecast"` — inside the panel subtitle itself: `"...descriptive history only, never a forecast or a promise."` This is the panel's own explicit anti-promise disclaimer (a negation), present identically on all 7 cards, not an assertion of forecasting. No other forbidden word appears anywhere in any panel. Treated as satisfying the intent of the check (the copy explicitly denies being a forecast).

### UT-03 — Below-floor streak insufficient, siblings real
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png`
- Card 1 Correction row: Longest-losing-streak cell = exactly `"insufficient (n=5)"`, rendered as `<span class="num text-text-faint">` (the codebase's muted-text utility class).
- Same row's other three cells: `"-10.75% (p90 -4.79%) n=250"`, `"20.0d (p90 20.0d) n=250"`, `"1.0d (p90 9.0d) n=149"` — all real, well-formed values; none reads "insufficient", "undefined", "NaN", or "null".

### UT-04 — Zero-observation cohort insufficient(n=0)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-04-card2-zero-obs.png`
- Card 2 ("Breakout-watch setup") confirmed badges "FAIL" + "Regime: Risk-on", Hypothesis chips `kind=event-study` / `subject=Breakout-watch`.
- Correction row: all 4 measure cells = exactly `"insufficient (n=0)"`. Bear row: all 4 measure cells = exactly `"insufficient (n=0)"`.
- No crash, no error boundary, no "undefined"/"NaN"/"null" anywhere. Expansion/Pullback/Recovery rows on the same card render normal real values (e.g. Expansion Max-DD `"-7.50% (p90 -3.57%) n=926"`) — degradation isolated to the two zero-observation rows only.

### UT-05 — Absent-panel contract check (best-effort)
**Verdict:** PASS
**Evidence:** direct `GET http://localhost:8255/api/evidence` fetch (see command output in session; no screenshot needed for this API-level check)
- **Methodology note:** rather than manually reading the DevTools Network-panel UI (which is awkward to evidence reliably through browser automation), this check was performed via an equivalent and more precise method — a direct fetch of the exact same endpoint the page's Network tab would show, cross-referenced against the DOM-level panel count from UT-01 (7/7 panels rendered, 0 missing).
- All 7 objects in `claims[]` carry a non-null, populated `expectations` object with keys `by_phase`, `horizon`, `method_note`, `min_sample`, `streak_min_n`, `survivorship_bias`; every `by_phase` array has exactly the 5 phases in order `Expansion, Pullback, Correction, Bear, Recovery`.
- Confirms today's live ledger does not exercise the "absent panel" rendering path (as the test plan itself anticipated) — that path remains unverified by direct observation this iteration; only the contract (non-null on all 7) is confirmed live.

### UT-06 — Existing field grid / verdict badges unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png`
- All 7 cards: `dt` labels = exactly `["Hypothesis","Out-of-sample verdict","Control comparison (vs SPY)","Registration date","Forward-walk score-to-date"]`, in that order (verified per-card, all 7/7 match).
- All 7 verdict badges read exactly "FAIL" (0/7 PASS, unchanged from before this phase).
- Panel count = exactly 1 per card on all 7 cards, and DOM-position-checked to always follow (never precede or interleave into) the existing `<dl>` field grid.
- Page-wide text search for `"+21.34%"`, `"+6.36%"`, `"p=0.0004998"` — zero matches. No stale pre-refresh values survive.

### UT-07 — Regime badge still correct
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-04-card2-zero-obs.png`
- Card 2's `evidence-claim-regime` badge reads exactly `"Regime: Risk-on"` — present, legible, positioned next to the FAIL badge.
- Dashboard cross-check (informational only, per the test's own acceptance bar): the dashboard's "Market Phase & Severity" card currently reads phase = "Expansion" (as of 2026-07-01) — legitimately different from the claim's own Risk-on regime scope, as the test plan explicitly allows.

### UT-08 — GO preflight strip unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-01-initial.png`
- `preflight-banner` text = exactly `"GO — today's board is current."`, visible directly below the top header bar, above the "Evidence" heading, not cut off or overlapped by any panel content.

### UT-09 — Stock deep-history chart controls
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-09-before-click.png`, `reports/qa/goal-mcp-loop-iter-41-evidence/UT-09-after-full-history.png`
- `/stocks/AAPL` heading = exactly "AAPL"; "Price & moving averages" card present with both `chart-range-recent` and `chart-range-full` buttons (`chart-range-control` wrapper present).
- Before click: caption = `"1255 bars · as of 2026-07-01 · history since 1996-01-02"`, `Recent` button `aria-pressed="true"`.
- After clicking `Full history`: caption = `"3185 bars · as of 2026-07-01 · history since 1996-01-02 · older bars weekly-sampled"`, `Full history` button `aria-pressed` flipped to `"true"`. Bar count rose 1255→3185 (2.5×) and a new "older bars weekly-sampled" clause appeared — both are strong, direct confirmation that deep multi-year history genuinely loaded on click.
- **Deviation from the test plan's literal wording, investigated and resolved:** the plan expected the "history since" date to move to "much earlier" after the click. It does not — it reads `1996-01-02` both before and after. Reading the frontend source (`apps/frontend/app/stocks/[ticker]/page.tsx:526-529`) confirms this is by design: the caption's "since" clause is bound to `state.data.first_available_date`, a fixed, ticker-level fact (the symbol's true real first bar) served identically regardless of which range mode is selected — not the start of the currently-rendered window. This is intentional honesty (always disclosing the ticker's real full extent), not a defect. The control's actual function — loading deeper history on click — is independently and directly confirmed by the bar-count jump and the new weekly-sampled clause, so the regression check's substance passes; only the test plan's specific predicted proxy-signal (which date field would move) was inaccurate.

### UT-10 — Data Manager page loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-10-data-manager.png`
- `h1` = exactly "Data Manager"; subtitle text begins "Grow the dataset on demand — view coverage and gaps, then fetch real EOD history"; "Dataset coverage" panel present; no blank page, no error message.

### UT-11 — Proven / Not yet proven badges
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-11-stocks-leaderboard.png`, `reports/qa/goal-mcp-loop-iter-41-evidence/UT-11-UT-12-aapl-scores.png`
- `/stocks`: every one of 1623 `evidence-badge` elements on the full leaderboard reads exactly "Not yet proven"; 0 read "Proven" — a comprehensive check across the whole rendered table, exceeding the test's "any row" bar.
- `/stocks/AAPL`: all 3 score cards (Leadership, Entry Quality, Risk) show the badge; `title` attribute on hover = `"Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."`

### UT-12 — Score-drill honest absence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-11-UT-12-aapl-scores.png`
- `score-proof-toggle` count on `/stocks/AAPL` = 0. No "Why proven?" button, no broken/empty box, no stuck spinner where a drill-down would go. Each card renders its score value and badge normally.

### UT-13 — Caveat visible + consistent wording
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-13-UT-14-card1-panel.png`
- `evidence-expectations-method-note` and `evidence-expectations-survivorship` on card 1: computed style `display:block`, `visibility:visible`, `max-height:none` — genuinely visible by scrolling alone, no accordion/tooltip-only reveal.
- Card 1 vs. card 3 text compared programmatically: both the method note and the survivorship caveat are byte-identical between the two cards, confirming server-provided, non-per-claim-authored copy.

### UT-14 — Phase-badge color gap (known minor)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-41-evidence/UT-13-UT-14-card1-panel.png`
- All 5 phase badges in card 1's expectations table (Expansion, Pullback, Correction, Bear, Recovery) share the exact identical CSS class string `"inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium transition-colors border-border bg-surface-2 text-text-muted"` — confirmed flat neutral gray with zero phase-conditional color differentiation, by class inspection (not just visual read).
- This exactly matches the gap already tracked as MINOR/cosmetic-only in `reports/reviews/goal-mcp-loop-iter-41-review.md` — confirmed no worse than documented. Not filed as a new bug, per the test's own instruction.

---

## Failed Tests

None. 14/14 executed test cases passed.

---

## Skipped Tests

None.

---

## Additional Observations (non-blocking, informational)

- **J-15 / J-16 test-coverage gap:** the phase spec's Definition of Done lists 10 required-still-passing journeys (J-01, J-02, J-04, J-05, J-11, J-10, J-13, **J-15, J-16**, J-20), but the UI test plan (`reports/phase-goal-mcp-loop-iter-41-ui-test-plan.md`) only authored UT cases for 8 of them — J-15 ("core pages/APIs stay fast, measured/budgeted") and J-16 ("data jobs are fast and honest about progress") have no corresponding UT-XX case in this plan, and this agent executes the given test plan rather than authoring new cases beyond it. J-15 is passively/incidentally consistent with everything observed this session — every page load and API call made during this run resolved quickly with no slow-load symptoms (e.g. `/api/evidence` ~5ms warm, all `await_text` waits resolved promptly) — but no dedicated timed benchmark was run against the committed budgets in `reports/perf-budgets.md`. J-16 (data-job progress honesty) was not exercised at all this session — no Fetch/Backfill job was triggered (triggering `/data`'s "Start" backfill action would kick off a real, multi-minute job against the live environment the coordinator asked not to be disturbed, so it was deliberately not attempted). Both are ordinarily measurement/reports-based journeys (`reports/perf-budgets.md`) rather than interactive click-path journeys — flagging for the coordinator/evaluator to cross-reference that report directly rather than relying on browser-qa for these two.
- **Console-log capture tooling gap:** `enable_console_logging` + `get_console_messages` were invoked but returned no messages; inspecting the Chrome MCP tool's own auto-captured `*-console.txt` session artifacts shows every one is a placeholder stub reading `"# TODO: Console logging not yet implemented"`. This means the "zero console errors" signal could not be independently confirmed via this tool this session — it is a tooling gap, not a verified clean-console finding. All PASS verdicts above rest on DOM/content/network evidence, not console-absence-of-errors, so this does not change any verdict, but it should not be read as "console was checked and was clean."
- **Golden replay script:** `runs/goal-session-mcp-loop/journey-scripts/J-25.json` was written and lint-passed (`demo_runner.py --mode lint` → `J-25 ok`) immediately after J-25's UT-01/UT-02 evidence was confirmed, per the golden-replay-script protocol. The 8 existing required-still-passing scripts (J-01, J-02, J-04, J-05, J-10, J-11, J-13, J-20) were spot-checked rather than blindly overwritten — J-01.json's assertions ("Stock Leaderboard", "541 / 541", "Not yet proven") were independently confirmed still accurate against the live `/stocks` page — but were deliberately left unmodified rather than rewritten wholesale: several of their steps involve actions this session did not replay end-to-end (e.g. J-13.json's step 2 clicks "Start", which would trigger a real, multi-minute backfill job against the live environment — deliberately not triggered, consistent with the coordinator's instruction not to disturb the running services), so overwriting them without full replay confidence would risk silently degrading an already-working golden. This is consistent with the golden-replay protocol's "best-effort... skip if you can't produce a clean script" allowance.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health path `/api/health`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`, CDP port 9222)
- **Test Date:** 2026-07-16
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-41-evidence/` (8 screenshots, all unique by md5 — no reused/blank frames)
- **Golden replay script:** `runs/goal-session-mcp-loop/journey-scripts/J-25.json` (new, lint-passed)
