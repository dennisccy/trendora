# Phase goal-mcp-loop-iter-36 — UI Test Results

**Phase:** goal-mcp-loop-iter-36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 13/13 tests passed (0 skipped)

All 7 P1 tests (UT-01, UT-03, UT-04, UT-05, UT-09, UT-10, UT-13) pass. All P2/P3 tests (UT-02, UT-06, UT-07, UT-08, UT-11, UT-12) also pass. See the UT-13 note below — its result required judgment because the ui-test-plan's literal "Expected Result" text does not match current product state; the discrepancy is documented in detail and the underlying substantive check (isolation) is independently corroborated by two additional live data points.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Referee-audit page loads without errors | smoke | P1 | Page renders (heading, subtitle, back-link, 4-card grid), no blank/404/error boundary, no console errors | All elements present and correct; no error boundary, no blank screen, no 404; console-message capture is unimplemented in this Chrome MCP build (verified via tooling, not a page defect) — zero visible errors via behavioral/visual proxy across every state tested in this session | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-01-result.png` |
| UT-02 | Loading skeleton renders before content | smoke | P3 | Pulsing 4-card skeleton grid appears before real content, fully replaced after fetch resolves | DevTools network throttling is not exposed as an action by this Chrome MCP tool (action enum has no throttle/CDP-override primitive); organically captured the skeleton mid client-side route transition instead — 4-card grid, 3 pulsing gray placeholder bars per card (title/value/subtext widths), same grid position as real content; immediately-following check showed full real content with no overlap | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-02-skeleton.png` |
| UT-03 | Stat summary grid shows exact calibration values | happy-path | P1 | Null trials 200 / "source factor: leadership_score"; false-pass rate 0.08 / "16 of 200 trials · 95% CI [0.04984, 0.126]"; α 0.05 / significance caption; run date 2026-07-01 / "seed 20240601 · contaminated horizon 5d" | All four cards show exactly the expected values and subtext, verbatim, immediately (no placeholders/spinners) | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-03-result.png` |
| UT-04 | Tripwire failure card renders for real live data | happy-path | P1 | Red-bordered/tinted card, warning-triangle icon, exact heading, red "PASS" badge, body text with "expected: rejected" + closing suspicion sentence, reason subtext, no calm card present | All exactly as expected; verified visually (red border/tint, red badge) and via full text extraction (heading, body, reason string byte-for-byte match) | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-04-result.png` |
| UT-05 | Contaminated badge never uses "Proven" styling | ux | P1 | Red "PASS" badge, never the accent/"Proven" color; no "Proven" text applied to the contaminated factor | Source-verified: `contaminatedStatusVariant()` always maps PASS/FAIL to `"danger"`, comment explicitly states "NEVER `accent`"; `Badge` variants confirm `danger`→`text-neg`(#f87171 red)/`accent`→`text-accent`(#4fd1c5 teal) are disjoint; `/evidence`'s shared "Proven" chip (`evidence-status-badge.tsx`) uses `variant="accent"`. Live page: badge renders red; only "proven" occurrence on the page is the subtitle's explicit disclaimer ("nothing here is a proven/not-proven signal"), never applied to the contaminated factor | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-05-result.png` |
| UT-06 | Calm confirmation card when factor is caught (fixture) | happy-path | P2 | Plain card, green shield-check icon, "Lookahead-contaminated factor: caught" heading, "Verdict: FAIL" badge (still red/danger), tripwire card absent | Backend restarted with `TRENDORA_REFEREE_AUDIT_PATH` pointed at a fixture (`status: FAIL`, `contaminated_caught: true`); page showed exactly this state; verified then reverted | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-06-result.png` |
| UT-07 | Honest empty state when no artifact exists | error | P2 | "No audit run yet" card; body explains offline-job invocation; no grid/verdict card; heading + back-link intact | Backend restarted pointed at a nonexistent path; API returned `{"report":null}` HTTP 200 (never 500); page showed exact expected card and body text; verified then reverted | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-07-result.png` |
| UT-08 | Unreadable artifact shows distinct amber state | error | P2 | Amber (not red) card, "Audit artifact unreadable" heading, re-run instruction, no grid/verdict card | Backend restarted pointed at a corrupt `not-json` file; API returned `status:"unreadable"` with nulls, HTTP 200; page showed amber-bordered card, exact expected text, visually distinct from both UT-04 (red) and UT-07 (plain); verified then reverted | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-08-result.png` |
| UT-09 | Backend unavailable shows contained card, nav intact | error | P1 | Contained red "Backend unavailable" card; page chrome (heading/subtitle/back-link) stays visible; no blank/crash page; "Back to Research" and further nav still work | Backend stopped entirely; page showed exact expected card, contained (not full-page takeover); clicked "Back to Research" → `/research` loaded; clicked "Certification-budget accounting" → `/research/budget` loaded (heading confirmed) — nav fully functional with backend down; global preflight banner also degraded honestly ("NO-GO — do not rely on today's board. Backend is unavailable…"); backend restarted clean afterward | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-09-result.png`, `UT-09-nav-after.png` |
| UT-10 | New "Referee audit" card discoverable and navigates | ux | P1 | Exactly 4 governance cards ending with "Referee audit" (shield-check icon, matching description); click navigates to `/research/referee-audit` and it loads | Confirmed 4 cards in order (registry, graveyard, budget, referee-audit); icon/heading/description match; clicked via `data-testid="research-governance-link-referee-audit"`, `window.location.href` confirmed `/research/referee-audit`, full content loaded correctly | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-10-before.png`, `UT-10-after.png` |
| UT-11 | Existing 3 governance cards unchanged | regression | P3 | Registry/graveyard/budget cards' text/icon/hover unchanged; each still navigates to its own page; order preserved, new card appended (not inserted) | Confirmed via `/research` page extraction + individually clicking each of the 3 (`data-testid="research-governance-link-{registry,graveyard,budget}"`) — each landed on its correct page with matching heading; Referee audit card sits 4th, after the other 3, own row | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-11-result.png` |
| UT-12 | Preflight banner still renders on new page | regression | P2 | "GO — today's board is current." quiet green banner above heading, single instance, present on other `/research/*` pages too | Confirmed present, single instance, correct text/styling on `/research/referee-audit`, `/research`, `/evidence`, and `/research/budget` | PASS | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-12-result.png`, `UT-12-budget-banner.png` |
| UT-13 | `/evidence` unchanged after audit ran (isolation) | regression | P1 | Per ui-test-plan wording: a single empty-state card, heading "No certified claims yet" | See detailed note below — actual state is 7 individual "FAIL" claim rows (0 "PASS"/"Proven" anywhere), which matches the phase spec's own DoD line ("0 PASS, 7 FAIL; no new claim appeared from the audit") rather than the ui-test-plan's literal wording. Substantive isolation criterion (no new claim leaked from the audit's 200+1 trials) independently corroborated by `git diff HEAD` (empty on all 3 real ledger files) and `/research/budget`'s "Total trials to date: 7 / Bonferroni divisor 8" (unchanged) | PASS (see note) | `reports/qa/goal-mcp-loop-iter-36-evidence/UT-13-result.png` |

---

## Passed Tests

### UT-01 — Referee-audit page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/research/referee-audit`. Heading "Referee audit" visible; subtitle beginning "Is the certifier itself calibrated?" visible directly below; "Back to Research" link with left-arrow icon visible above the heading; 4-card stat grid visible below heading (settled/loaded state, not stuck loading). No blank screen, no Next.js error boundary, no 404.
- Console-error verification note: this Chrome MCP build's console capture is unimplemented (`enable_console_logging` + `get_console_messages` consistently returned "No console messages captured"; the auto-captured `*-console.txt` sidecar file literally contains `# TODO: Console logging not yet implemented`). This is a tooling limitation, not a page defect — I used the presence of fully-correct rendered content and the absence of any error-boundary/blank-page state (checked across all 7 distinct page states exercised in this session: loaded/skeleton/tripwire/calm/empty/unreadable/backend-down) as the practical proxy for "no errors."

### UT-02 — Loading skeleton renders before content
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-02-skeleton.png`
- This Chrome MCP tool's action set (`navigate, click, type, extract, screenshot, eval, select, attr, await_element, await_text, ...`) has no network-throttling/CDP-override primitive, so the literal "DevTools → Network → Slow 3G" step could not be performed. Instead, the skeleton state was captured organically: clicking the new "Referee audit" nav card (a Next.js client-side route transition) landed mid-fetch, and the screenshot at that instant shows a 4-card grid with 3 pulsing gray placeholder bars per card (title-width, value-width, subtext-width), in the exact same grid position the real stat grid later occupies. A follow-up check (`extract`) immediately after showed the skeleton fully replaced by real content with no overlap and no indefinite stall.

### UT-03 — Stat summary grid shows exact calibration values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-03-result.png`
- "Null trials": **200**, subtext "source factor: leadership_score".
- "Empirical false-pass rate": **0.08**, subtext "16 of 200 trials · 95% CI [0.04984, 0.126]".
- "Configured α": **0.05**, subtext "the significance level the null trials are judged against".
- "Run date": **2026-07-01**, subtext "seed 20240601 · contaminated horizon 5d".
- All four values verbatim-matched the live `GET /api/research/referee-audit` response (`curl`-verified independently) and appeared with no "—" placeholders or perpetual spinners.

### UT-04 — Tripwire failure card renders for real live data
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-04-result.png`
- Red-bordered card with light-red/pink tint (`border-neg bg-neg/10` per source) visible directly below the stat grid.
- Heading exactly: "Tripwire: the lookahead-contaminated factor was NOT rejected", warning-triangle icon to its left.
- Badge reads "PASS", styled red/danger (never blue/accent).
- Body paragraph includes "expected: rejected" and ends with "...treat every certified claim from this basis with suspicion until this is investigated." (verbatim).
- Smaller reason line: "certified: holdout edge +0.0914 beats the control out-of-sample and is significant after multiple-testing deflation (p=0.0004998 < alpha/1=0.05)" (verbatim).
- No calm/green confirmation card present anywhere on the page.

### UT-05 — Contaminated badge never uses "Proven" styling
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-05-result.png`
- Checked `/evidence` first for the accent/"Proven" color reference; at present `/evidence` shows no live "Proven" badge instance (all 7 registered claims currently read FAIL — see UT-13), so the color reference was confirmed at the source/design-token level instead of a live badge: `apps/frontend/app/globals.css` defines `--accent: #4fd1c5` (teal) vs `--neg: #f87171` (red); `components/ui/badge.tsx` maps `accent` → `text-accent` and `danger` → `text-neg`; `components/evidence-status-badge.tsx` (the shared "Proven" chip used elsewhere in the product, e.g. stocks page) explicitly uses `variant="accent"`.
- `apps/frontend/app/research/referee-audit/page.tsx`'s `contaminatedStatusVariant()` returns `"danger"` for both `PASS` and `FAIL` statuses and is commented "mapped to `danger`, NEVER `accent` (this page must never render a 'Proven'-looking badge, anti-goal #1)".
- Live page: the "PASS" badge renders in the red/danger family, visibly distinct from the teal accent color.
- Full-page text extraction shows the only occurrence of "proven" is in the subtitle's disclaimer sentence ("nothing here is a proven/not-proven signal") — an explicit denial, not a status applied to the contaminated factor. No "Proven" text anywhere describes the contaminated factor's result.
- The "PASS" badge sits immediately next to "expected: rejected" in the body text, making the bad-news framing immediately legible.

### UT-06 — Calm confirmation card when factor is caught (fixture)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-06-result.png`
- Built a fixture (copy of the real artifact with `contaminated_verdict.status` changed `PASS`→`FAIL`, `contaminated_caught` set `true` to match the harness's own derivation logic `status != "PASS"`).
- Stopped the backend (`fuser -k 8255/tcp`), restarted with `TRENDORA_REFEREE_AUDIT_PATH=<fixture> ./scripts/start-backend.sh`; confirmed via `curl` the API served `status:"FAIL"` before checking the browser.
- Page showed: plain (non-red) card, green shield-check icon, heading "Lookahead-contaminated factor: caught"; body "...was submitted to the referee — expected: rejected. Verdict: **FAIL**" with the FAIL badge still rendered in red/danger (not blue/accent — consistent with UT-05, even a "correct" verdict badge isn't styled as Proven); the UT-04 red tripwire card was absent.
- **Reverted:** stopped the fixture backend and restarted clean before proceeding.

### UT-07 — Honest empty state when no artifact exists
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-07-result.png`
- Restarted backend with `TRENDORA_REFEREE_AUDIT_PATH` pointed at a path confirmed not to exist; `curl` confirmed the API returned `{"report":null}` with HTTP 200 (never 500).
- Page showed a card headed "No audit run yet"; body text: "The referee-calibration harness has not been run yet. It runs as a config-seeded offline job (`python -m app.engine.referee_audit`), never as a UI action here — once it runs, its persisted report appears on this page." No stat grid, no verdict card, no error boundary, no blank page. Page heading and "Back to Research" link remained visible above the card.
- **Reverted:** stopped and restarted the backend clean before proceeding.

### UT-08 — Unreadable artifact shows distinct amber state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-08-result.png`
- Created a file containing the literal text `not-json`; restarted backend pointed at it; `curl` confirmed the API returned `{"report":{"status":"unreadable", ...all other fields null...}}` with HTTP 200 (never 500).
- Page showed an amber/yellow-bordered card (visibly distinct from both the red UT-04 tripwire card and the plain UT-07 empty-state card) headed "Audit artifact unreadable"; body: "A referee-audit report exists but could not be parsed. Re-run the offline harness (`python -m app.engine.referee_audit`) to regenerate it." No stat grid, no verdict card.
- **Reverted:** stopped and restarted the backend clean before proceeding.

### UT-09 — Backend unavailable shows contained card, nav intact
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-09-result.png`, `reports/qa/goal-mcp-loop-iter-36-evidence/UT-09-nav-after.png`
- Stopped the backend entirely (`fuser -k 8255/tcp`); confirmed connection failure via `curl` (`HTTP 000`).
- Reloaded `/research/referee-audit`: a red-bordered, contained card appeared reading "Backend unavailable" / "The referee-audit report could not load from the API. Confirm the backend is running and reload." — verbatim match. Page heading, subtitle, and "Back to Research" link remained visible above the card; no blank white screen, no unhandled crash page.
- Bonus: the global cross-cutting preflight banner (J-20) also degraded honestly to "NO-GO — do not rely on today's board. Backend is unavailable — the preflight check could not run." rather than breaking — reinforcing the anti-goal #8 resilience requirement holds at both layers.
- Clicked "Back to Research" (XPath text match) → `window.location.href` confirmed `/research` loaded correctly. Clicked "Certification-budget accounting" card → confirmed navigation to `/research/budget` (heading "Certification-budget accounting" rendered) — the rest of the site continues to attempt normal navigation with the backend down.
- **Reverted:** restarted the backend clean (no env override) before proceeding; confirmed HTTP 200 with the real artifact restored.

### UT-10 — New "Referee audit" card discoverable and navigates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-10-before.png`, `reports/qa/goal-mcp-loop-iter-36-evidence/UT-10-after.png`
- `/research` → "Governance & process" section shows exactly 4 cards in order: "Pre-registration registry," "Negative-results graveyard," "Certification-budget accounting," "Referee audit."
- 4th card: shield-check icon, heading "Referee audit," description beginning "Is the certifier itself calibrated?" — same card styling/hover treatment as its 3 siblings (visually confirmed).
- Clicked via `[data-testid="research-governance-link-referee-audit"]`; `window.location.href` eval confirmed `http://localhost:3255/research/referee-audit`; page loaded successfully with full real content (heading + 4-stat grid + tripwire card), not a dead link or 404.

### UT-11 — Existing 3 governance cards unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-11-result.png`
- Confirmed heading/description text for "Pre-registration registry," "Negative-results graveyard," "Certification-budget accounting" via page text extraction — matches the descriptions used throughout the governance cluster's prior iterations.
- Clicked each individually via `data-testid="research-governance-link-{registry,graveyard,budget}"`, confirming via `window.location.href` + rendered heading: registry → `/research/registry` ("Pre-registration registry"), graveyard → `/research/graveyard` ("Negative-results graveyard"), budget → `/research/budget` ("Certification-budget accounting"). No 404s, no errors.
- Card order confirmed unchanged; "Referee audit" was appended as the 4th card (own row after the 3x3 grid wraps), not inserted between the existing 3.

### UT-12 — Preflight banner still renders on new page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-12-result.png`, `reports/qa/goal-mcp-loop-iter-36-evidence/UT-12-budget-banner.png`
- "GO — today's board is current." banner, quiet green-tinted strip, visible at the very top of `/research/referee-audit`, above the page heading — single instance, no overlap, no duplication.
- Cross-checked and confirmed present with identical text/styling on `/research`, `/evidence`, and `/research/budget`.

### UT-13 — `/evidence` unchanged after audit ran (isolation)
**Verdict:** PASS (see note — required judgment; ui-test-plan wording did not match actual state)
**Evidence:** `reports/qa/goal-mcp-loop-iter-36-evidence/UT-13-result.png`

**Note on discrepancy between the ui-test-plan's expected wording and actual observed state:**

The ui-test-plan's literal "Expected Result" describes a *single empty-state card* with heading "No certified claims yet" and states "no individual claim row appears anywhere on the page." That is **not** what `/evidence` actually shows. The actual, observed state is:
- Page heading "Evidence"; subtitle "The certified-claims ledger — the single source of proven-ness. A signal reads "Proven" ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else honestly reads "Not yet proven."" — this part matches the ui-test-plan.
- Below that: **7 individual claim rows** (`leadership_score`, `Breakout-watch setup`, `ma_stack — top decile (D10)`, `vcp_contraction — top decile (D10)` ×2 distinct hypotheses, `rs_spy_3m × high_proximity — composite`, `rs_spy_3m — top decile (D10)`), **every one badged "FAIL"**. Zero "PASS" badges, zero "Proven" badges anywhere on the page (full-text extraction confirmed).

This exactly matches the phase spec's own Definition of Done line, which is the more authoritative source for what "unchanged" should look like this iteration: *"`/evidence` renders unchanged (0 PASS, 7 FAIL; no new claim appeared from the audit) — browser-verified (J-22 step 4)."* The OUT OF SCOPE section similarly pre-states *"both real ledgers stay 7/7 FAIL and byte-identical."* Both independently describe the exact state observed — i.e., this 7-row/0-PASS state is the pre-existing baseline from earlier iterations' registry work (J-18/J-19), not something new, and the ui-test-plan's "single empty-state card" wording appears to be stale/incorrect (most likely inherited from an earlier point in the session before the registry was populated).

**What this test exists to verify — isolation — was independently confirmed three ways:**
1. Exactly 7 claim rows, 0 "PASS"/"Proven" anywhere: matches the DoD's stated unchanged baseline precisely (not 207 or 208 rows, not a new 8th row).
2. `git diff HEAD -- '**/certified-claims.jsonl' '**/staging-ledger.jsonl' '**/pre-registrations.jsonl'` → **empty output** (no modifications to any of the three real dominant-failure-mode files), confirmed at the filesystem/VCS level, independent of the browser.
3. `/research/budget` (loaded during UT-12's cross-page banner check) shows "Total trials to date: 7 / Next canonical trial will be #8" and "Current canonical required p = 0.00625 = 0.05 ÷ 8 (Bonferroni)" — if the audit's 200 null trials + 1 contaminated trial had leaked into the canonical ledger/budget accounting, this counter and divisor would not still read 7/8.

Given the substantive isolation guarantee is confirmed by three independent signals (page content, git diff, and the budget page's own live counters), I am recording UT-13 as **PASS** on its substantive intent, while flagging the ui-test-plan wording mismatch explicitly here for the ui-test-designer/auditor's awareness — this is a test-plan authoring note, not a product defect.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available for the full test run.

---

## Additional notes for the pipeline (not gating this verdict)

- **Golden replay script written for J-22:** per the browser-qa-agent's golden-replay-script mandate, `runs/goal-session-mcp-loop/journey-scripts/J-22.json` was written after all UT-XX tests passed (happy-path click-through from `/research` → the new card → `/research/referee-audit`, asserting the null-trial subtext, false-pass-rate/CI text, "expected: rejected," and the run date). Linted clean (`demo_runner.py --mode lint`) and **live-replayed PASS** (`demo_runner.py --mode verify --journeys J-22` against `http://localhost:3255`) before this report was written.
- **Required-still-passing set out of my dispatched scope:** the phase spec's Definition of Done additionally requires J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20 to be "LIVE-re-verified via the browser-qa lane" this iteration. My dispatched `reports/phase-goal-mcp-loop-iter-36-ui-test-plan.md` contains only UT-01 through UT-13, all scoped to J-22 and its directly-touched regression surfaces (governance cards, preflight banner, evidence isolation) — it does not contain separate UT-XX cases for that required-still-passing set, so I did not fabricate coverage for journeys outside my assigned test plan. For visibility: `runs/goal-session-mcp-loop/journey-scripts/` already holds golden scripts for all 8 of those journeys, and `runs/goal-session-mcp-loop/state/journey-history.json` records all 8 as `"status": "passing"` (last verified iter-34/iter-35). Whether that DoD line is satisfied via a fresh live re-verification or a golden-script replay pass is a decision for the auditor/goal-evaluator step, not something I ran myself since it fell outside my dispatched test plan.
- **Console-message capture limitation:** this Chrome MCP build does not implement console-message capture (`get_console_messages` always returns empty; the auto-generated `*-console.txt` sidecar literally says "TODO: Console logging not yet implemented"). This affected only the console-error sub-check inside UT-01; it did not block completion of any test. Flagging for whoever maintains the Chrome MCP plugin.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-36-evidence/`
- **Build freshness:** `apps/frontend/.next/BUILD_ID` (2026-07-14 23:19:00) confirmed to postdate both `apps/frontend/app/research/referee-audit/page.tsx` (23:13:14) and `apps/frontend/app/research/page.tsx` (23:13:33) — stale-build trap (iter-20/21/35) does not apply.
- **Backend state:** confirmed restored to default (real committed artifact, no env override) and both services healthy (HTTP 200) after test completion.
