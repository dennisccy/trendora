# Phase goal-mcp-loop-iter-31 — UI Test Results

**Phase:** goal-mcp-loop-iter-31 (goal mode, journey J-19 / backlog B-902)
**Date:** 2026-07-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-07 (P1, happy-path) failed. Per verdict rule: "FAIL: Any smoke test fails, OR any
     happy-path test fails, OR any P1 test fails." -->

**Overall:** 11/14 tests passed (1 failed, 2 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/research/graveyard` loads directly, structure present | smoke | P1 | Back-to-Research link, heading, subtitle, 6-column table header, Revisit-protocol panel, no error page/console error | All structural elements present exactly as specified; page rendered cleanly | PASS | `UT-01-loaded.png` |
| UT-02 | CENTERPIECE: discover from hub + all 14 rows correct incl. byte-exact ma_stack | happy-path | P1 | 1 click from `/research` to graveyard; 14 rows (7 canonical/7 staging); ma_stack row FAIL/2026-07-03 matching ledger byte-for-byte | Card clicked → navigated to `/research/graveyard`; 14 rows confirmed (7/7 split); ma_stack row's selectors/verdict/date/reason matched `certified-claims.jsonl` raw JSON exactly | PASS | `UT-02-hub-governance.png`, `UT-02-all-14-rows.png` |
| UT-03 | Selectors render as chips, never raw JSON; dates yyyy-MM-dd | validation | P2 | 5 pill chips for the named staging combination row, no braces/brackets; dates plain `yyyy-mm-dd`; noted 3-row `ledger=canonical` quirk not a bug | Row read exactly `cohort=composite`, `condition=rs_spy_3m:top:quintile+high_proximity:top:tertile`, `direction=positive`, `horizon=20`, `kind=combination` as 5 chips; all dates `2026-07-03`; the extra `ledger=canonical` chip appeared on exactly the 3 rows the plan names | PASS | `UT-02-all-14-rows.png` |
| UT-04 | Verdict badges FAIL/INSUFFICIENT only, never accent/"Proven" | validation | P1 | All 14 badges red FAIL/amber INSUFFICIENT; no "Proven"/accent styling; word "Proven" absent from page | All 14 badges "FAIL", class `border-neg ... text-neg` (not `accent`); "permanent" badge uses neutral `text-text-faint`; page text contains zero occurrences of "Proven" (case-sensitive) and no literal "PASS" | PASS | `UT-02-all-14-rows.png` (DOM class check via eval) |
| UT-05 | Deflation context verbatim for both ledgers | validation | P2 | canonical leadership_score h20 → `bonferroni ÷1`; staging vcp_contraction h10 → `lord++ ÷1` | Both cells read exactly as expected; no recomputed p-value/percentage in the Deflation column | PASS | `UT-02-all-14-rows.png` |
| UT-06 | ma_stack "permanent" marking in-frame, unique to that row | happy-path | P1 | ma_stack row shows muted "permanent" badge beside FAIL, both in-frame; no other row shows it | Confirmed on dedicated screenshot: "permanent" badge beside "FAIL" in same cell, uncropped; the other 13 rows have no such badge | PASS | `UT-06-ma_stack-permanent.png` |
| UT-07 | Lineage link resolves + scrolls to exact registry row | happy-path | P1 | Click navigates to `/research/registry#registration-factor-ma_stack-d10-h20` (no `?asof=`) AND auto-scrolls so the target row sits just below the header | URL resolved correctly (confirmed via `window.location.href`) and the target `<tr id="registration-factor-ma_stack-d10-h20">` exists in the DOM — but `window.scrollY` stayed at exactly `0` after the click, confirmed twice (once immediately, once after an explicit 1.5s wait); no auto-scroll occurred | **FAIL** | `UT-07-FAIL-no-scroll.png` |
| UT-08 | Revisit-protocol panel + every row's anchor link | happy-path | P2 | Panel text exact match; every row has "Revisit protocol →" link; clicking one scrolls the panel into view | Panel text matched exactly; all 14 rows carry the link; clicking scrolled `window.scrollY` from 0 to 948 (the document's maximum scroll extent) and `getBoundingClientRect()` confirmed the panel (`top:1066,bottom:1176`) sits inside the 1200px viewport | PASS | `UT-08-revisit-protocol-scroll.png` (see note below on screenshot limitation) |
| UT-09 | Backend unavailable → one contained error card | error | P1 | Contained "Backend unavailable" card, red border, warning icon; heading/back-link/sidebar still functional; recovers cleanly on restart | Backend stopped → reload showed exactly the specified contained error card, heading and Back-to-Research link intact, sidebar fully clickable, no blank/crash page; backend restarted → reload showed the real 14-row table with no leftover error state | PASS | `UT-09-backend-unavailable.png` |
| UT-10 | Missing/empty ledgers → honest empty state, no crash | error | P1 | Renaming both ledger files → calm "No rejected hypotheses yet" empty-state card | **Not executed** — see Skipped Tests | SKIP | none |
| UT-11 | Loading skeleton (8 bars) shown, then fully replaced | smoke | P2 | 8-bar pulsing skeleton visible under network throttling, then fully replaced | **Not executed** — see Skipped Tests | SKIP | none |
| UT-12 | Hub lab grid + registry card unchanged; graveyard card 2nd | regression | P2 | Exactly 10 unchanged lab cards; exactly 2 governance cards in order; unchanged registry description; new graveyard description exact | Confirmed all 10 lab-grid card titles/order unchanged; exactly 2 governance cards (Pre-registration registry, then Negative-results graveyard) with both description strings matching verbatim | PASS | `UT-02-hub-governance.png` |
| UT-13 | `/research/registry` + `/evidence` unaffected under normal browsing | regression | P1 | Registry: 11 rows/5 columns unchanged; direct-URL fragment scroll works standalone; Evidence: 7 FAIL cards unchanged | Registry plain-URL browsing showed 11 rows/5 columns as before; typing the fragment URL directly (no graveyard link involved) correctly scrolled `ma_stack`'s row beneath the header; `/evidence` showed exactly 7 claim cards, all "FAIL", content byte-identical to pre-iteration expectations | PASS | `UT-13-registry-plain.png`, `UT-13-registry-anchor-direct.png`, `UT-13-evidence-page.png` |
| UT-14 | Discoverable in ≤2 clicks from Dashboard, clear label | ux | P2 | Dashboard → Research (click 1) → Graveyard card (click 2); sidebar unchanged, 7th item; plain-language card copy | Confirmed sidebar order (11 items, Research 7th, unchanged); click 1 → `/research`; click 2 (card) → `/research/graveyard`; card copy is plain language, no internal jargon | PASS | (URL/heading confirmed via eval; see `UT-02-hub-governance.png` for card copy) |

---

## Passed Tests

### UT-01 — `/research/graveyard` loads directly, structure present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-01-loaded.png`
- "Back to Research" link with left-arrow icon above the title; heading "Negative-results graveyard"; subtitle begins "Every hypothesis the statistical referee has rejected — out-of-sample FAIL or INSUFFICIENT, across both the canonical and internal staging ledgers" (exact match).
- Table header row reads, left to right: Selectors, Verdict, Date, Deflation, Ledger, Lineage (6 columns, exact order).
- "Revisit protocol" panel visible below the table (confirmed via page-text extraction).
- No blank page, no browser error page. Checked for a Next.js error-overlay DOM node via `eval` (`document.querySelector('[data-nextjs-dialog], nextjs-portal, #__next-build-watcher')`) — none found.
- Console-error check: the Chrome MCP tool's console capture is not implemented in this environment (`# TODO: Console logging not yet implemented` in every `*-console.txt` capture, and `enable_console_logging` did not yield any captured messages across repeated attempts). This is a tool limitation, not a page issue — noted here rather than silently assumed clean. Corroborating signal (no error overlay, fully-formed real content, functioning interactivity throughout the whole session) supports no blocking JS error occurred.

### UT-02 — CENTERPIECE: discover from hub + all 14 rows correct incl. byte-exact ma_stack
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-hub-governance.png`, `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-all-14-rows.png`
- From `/research`, the "Governance & process" heading has exactly 2 cards: "Pre-registration registry" (book icon, first) and "Negative-results graveyard" (archive icon, second).
- Clicking the graveyard card navigated directly to `/research/graveyard` (1 click from the hub).
- Table rendered exactly 14 data rows (`data-testid="graveyard-row"` count = 14, confirmed via `eval`); 7 tagged "canonical" and 7 tagged "staging" in the Ledger column.
- All 14 Verdict badges read "FAIL" (none "INSUFFICIENT" today, matching the live-data expectation).
- The row with Selectors `decile=10 direction=positive factor=ma_stack horizon=20 kind=factor slice_kind=decile` showed Verdict "FAIL" and Date "2026-07-03". Cross-checked directly against `runs/goal-session-mcp-loop/state/certified-claims.jsonl`'s raw JSON for the `ma_stack` entry: `register_date: "2026-07-03"`, `verdict.status: "FAIL"`, `verdict.reason` begins "holdout edge +0.002062 is not significant after multiple-testing deflation" — the UI's displayed reason text reads exactly "holdout edge +0.002062 is not significant after multiple-testing deflation (p=0.2769 >= alpha/3=0.01667)", a byte-exact match to the ledger's `reason` field.
- No cell in any row was blank or read "undefined".

### UT-03 — Selectors render as chips, never raw JSON; dates yyyy-MM-dd
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-all-14-rows.png`
- The staging combination row (Ledger="staging", Deflation="lord++ ÷7") shows exactly 5 separate pill chips: `cohort=composite`, `condition=rs_spy_3m:top:quintile+high_proximity:top:tertile`, `direction=positive`, `horizon=20`, `kind=combination` — the two condition legs joined with a single `+`, no bracketed array, no raw JSON/braces anywhere in the cell.
- All 14 Date cells read `2026-07-03` in plain form, never a raw timestamp.
- The 3-row `ledger=canonical` extra-chip quirk the test plan pre-disclosed (vcp_contraction+h60, rs_spy_3m+h60, and the canonical-tagged combination/h20 row) is present on exactly those 3 rows and no others — confirmed, not flagged as a bug per the plan's own note.

### UT-04 — Verdict badges FAIL/INSUFFICIENT only, never accent/"Proven"
**Verdict:** PASS
**Evidence:** DOM class inspection via `eval` (see below); `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-all-14-rows.png`
- All 14 Verdict badges read "FAIL"; class attribute `inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium transition-colors border-neg bg-surface-2 text-neg` — a distinct "neg" (red/negative) styling token, not the `accent` (green/"Proven") token `/evidence` uses for PASS.
- The "permanent" badge uses `border-border bg-surface-2 text-text-faint` — neutral/muted, not accent.
- Page-text search for the literal substring "Proven" (case-sensitive) returned zero matches; the literal "PASS" also does not appear anywhere on the page.
- Subtitle ends "...nothing here is a proven/not-proven signal." (lowercase, descriptive usage only — matches the page's own honesty-fence framing, not a "Proven" badge claim).

### UT-05 — Deflation context verbatim for both ledgers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-all-14-rows.png`
- Canonical row (`factor=leadership_score`, `horizon=20`): Deflation cell reads exactly `bonferroni ÷1`.
- Staging row (`factor=vcp_contraction`, `horizon=10`): Deflation cell reads exactly `lord++ ÷1`.
- Both are plain policy-name-plus-divisor text; no recomputed p-value/percentage appears in this column (p-values, where shown, are in the small reason text under the Verdict badge, a separate cell).

### UT-06 — ma_stack "permanent" marking in-frame, unique to that row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-06-ma_stack-permanent.png`
- The `factor=ma_stack` row shows a small muted "permanent" badge immediately beside its red "FAIL" badge, both fully in-frame in a single uncropped screenshot, in the same cell.
- Scanned all other 13 rows (via full-page text/DOM extraction) — none carry a "permanent" badge. It appears on exactly one row.

### UT-08 — Revisit-protocol panel + every row's anchor link
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-08-revisit-protocol-scroll.png` (screenshot caveat below); DOM measurements via `eval`
- Panel heading "Revisit protocol" with body text matching exactly: "A referee FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a materially changed precondition (a new data span covering ≥2 additional OOS years, a data-basis change, or a genuinely different hypothesis) and must be registered as a NEW candidate citing the closed verdict."
- All 14 rows carry a "Revisit protocol →" link (confirmed via text extraction).
- Clicking a row's link changed the URL hash to `#revisit-protocol` and moved `window.scrollY` from `0` to `948` — the document's maximum possible scroll extent (`document.documentElement.scrollHeight` 2148 − `window.innerHeight` 1200 = 948, confirmed exactly), i.e., the click scrolled as far as the page physically allows. `getBoundingClientRect()` on `#revisit-protocol` at that scroll position returned `top:1066, bottom:1176`, fully inside the `[0,1200]` viewport — the panel is genuinely in view.
- **Screenshot caveat:** repeated `screenshot` calls taken after this scroll (6 separate attempts, including one from the click action's own auto-capture) all rendered a frame visually consistent with `scrollY≈0` instead of the DOM-confirmed `948`, even though `window.scrollY` read `948` via `eval` immediately before/after each attempt. A control test (`window.scrollTo(0,500)` then `screenshot`) produced a screenshot correctly matching `500`, and screenshots taken via the `navigate` action (full page loads, e.g. UT-09's backend-down capture) were reliably accurate — so this appears to be a rendering-sync quirk specific to this tool's `screenshot` action after JS/click-driven in-page scrolling, not a product defect. Verdict is based on the authoritative DOM measurements (`window.scrollY`, `getBoundingClientRect`), which are standard browser APIs read via live `eval` execution, not on the visually-inconclusive screenshot.

### UT-09 — Backend unavailable → one contained error card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-09-backend-unavailable.png`
- With the graveyard confirmed loading normally, the backend process was stopped (`kill -TERM` on the uvicorn PID; confirmed via `curl` returning no connection and `ps -p` confirming the process gone).
- Reloading `/research/graveyard` showed exactly: a card headed "Backend unavailable" with body "The graveyard could not load from the API. Confirm the backend is running and reload.", red-tinted border, warning-triangle icon.
- The "Negative-results graveyard" heading and "Back to Research" link still rendered above the error card; the error was contained to the data area only.
- No blank page, no browser network-error page, no unhandled JS error overlay. The left sidebar (all 11 items) remained visible and normally styled/clickable. The top-right status pill also correctly flipped to a red "Backend unavailable" indicator (a bonus consistency signal beyond what the test required).
- Backend was restarted via `scripts/start-backend.sh` (confirmed listening + serving 200 on `/api/research/graveyard`); reloading the page showed the real 14-row table again with `data-testid="graveyard-row"` count = 14, and no leftover "Backend unavailable" or empty-state text found in the page body.

### UT-12 — Hub lab grid + registry card unchanged; graveyard card 2nd
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-02-hub-governance.png`
- Main lab grid above "Governance & process" has exactly 10 cards, same titles/order as expected: Factor Lab, Regime Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Regime × Setup × Pattern, Severity-velocity × Regime, Multi-factor combination, Setup & Pattern event study, Recovery-Turn Edge, Downtrend Opportunity.
- "Governance & process" has exactly 2 cards in order: "Pre-registration registry" (book icon), then "Negative-results graveyard" (archive icon).
- "Pre-registration registry" description still ends "...The gate refuses to certify anything that isn't here." (unchanged).
- "Negative-results graveyard" description reads exactly "Every hypothesis the referee has rejected, across the canonical and staging ledgers — its verdict, deflation context, and registration lineage. Nobody retries a dead idea blindly."

### UT-13 — `/research/registry` + `/evidence` unaffected under normal browsing
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-13-registry-plain.png`, `reports/qa/goal-mcp-loop-iter-31-evidence/UT-13-registry-anchor-direct.png`, `reports/qa/goal-mcp-loop-iter-31-evidence/UT-13-evidence-page.png`
- `/research/registry` (plain URL, no fragment) showed its usual 11 rows across all 5 columns (Selectors, Rationale, Registered, Source, Status), populated exactly as expected.
- Typing `/research/registry#registration-factor-ma_stack-d10-h20` directly into the address bar (a hard navigation, not arrived at via a graveyard link) correctly scrolled the page so the `ma_stack` ("closed" status) row was positioned just below the sticky header — confirmed both visually (screenshot) and via DOM (`getElementById` + non-zero `scrollY`). This proves the underlying anchor mechanism (`id="registration-..."` + `scroll-mt-20`) works correctly on its own; see the UT-07 write-up for the separate finding that the SPA client-side link click does not trigger it.
- `/evidence` showed exactly 7 claim cards, every one with a red "FAIL" badge, content (hypothesis text, holdout-edge values, reasons) matching the pre-iteration expectations verbatim. This confirms `apps/backend/main.py`'s new `graveyard.router` registration did not break backend startup or the pre-existing `/evidence` page.

### UT-14 — Discoverable in ≤2 clicks from Dashboard, clear label
**Verdict:** PASS
**Evidence:** confirmed via `eval` (`window.location.href`, `document.querySelector('h1')`) at each step; card copy visible in `UT-02-hub-governance.png`
- From `/` (Dashboard), the left sidebar reads, in order: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, **Research** (7th), Evidence, Watchlist, Methodology, Data Manager — unchanged, no new/reordered entry.
- Click 1 ("Research" nav item) → `http://localhost:3255/research` (confirmed).
- The "Governance & process" heading and its two cards are reached by ordinary scroll, no submenu/tab/search needed.
- Card title "Negative-results graveyard" and its one-line description use plain language ("hypothesis the referee has rejected", "verdict, deflation context, and registration lineage") — no internal jargon such as "non-PASS" appears in the card copy.
- Click 2 (the card) → `http://localhost:3255/research/graveyard` (confirmed via `h1` = "Negative-results graveyard"). Total: 2 clicks from the Dashboard.

---

## Failed Tests

### UT-07 — Lineage link resolves + scrolls to exact registry row
**Verdict:** FAIL
**Failure:** Clicking a graveyard row's Lineage link correctly navigates to the right URL (including the correct `#registration-<id>` fragment, no stray `?asof=`), and the target row exists in the DOM at that id — but the page does **not** auto-scroll to bring the target row into a "just below the header" position. `window.scrollY` remains exactly `0` after the click, both immediately and after an explicit 1.5-second wait. This directly contradicts the test's explicit acceptance criterion: "No broken link, no 404, no landing on the page top with the target row unreachable without manual scrolling/searching" — the click does land the user at the page top, with no scroll assist to the target row.
**Evidence:** `reports/qa/goal-mcp-loop-iter-31-evidence/UT-07-FAIL-no-scroll.png`

**Steps taken:**
1. Navigated fresh to `http://localhost:3255/research/graveyard` (live/default as-of date, no historical date selected).
2. Located the `ma_stack` row and clicked its Lineage link, which read exactly `factor-ma_stack-d10-h20 →` (matching the expected link text).
3. Immediately queried `window.location.href` and `document.querySelector('h1').textContent` via `eval`.
4. Queried `window.scrollY` via `eval`, then again after an in-page `setTimeout` of 1500ms (executed in real page time, not just tool round-trip delay).
5. Queried `document.getElementById('registration-factor-ma_stack-d10-h20')` and its `getBoundingClientRect()` to confirm the anchor target genuinely exists in the DOM.
6. Repeated the entire sequence (fresh navigate → click → eval) a second time from scratch to rule out a one-off fluke; result was identical both times.
7. As a control, separately loaded the exact same target URL (`/research/registry#registration-factor-ma_stack-d10-h20`) via a **hard/full navigation** (typing the URL directly, per UT-13 step 3) — that path correctly scrolled the row into position just below the header (screenshot: `UT-13-registry-anchor-direct.png`), proving the anchor mechanism itself (`id` + `scroll-mt-20`) works; the gap is specific to the client-side (SPA) navigation triggered by clicking the Lineage link from the graveyard page.

**Expected:** URL becomes `http://localhost:3255/research/registry#registration-factor-ma_stack-d10-h20` AND the page scrolls so the `ma_stack` row is positioned just below the sticky header.
**Actual:** URL correctly becomes `http://localhost:3255/research/registry#registration-factor-ma_stack-d10-h20` (heading correctly updates to "Pre-registration registry"), but `window.scrollY` stays at `0` — no scroll occurs. The target row is not brought into a "below the header" position; it merely happens to be reachable without scrolling in this particular case only because `ma_stack` is the 3rd of 11 registry rows and fits within the initial viewport on a 1200px-tall screen — the same underlying gap would leave a row further down the registry table (e.g. the 9th–11th rows) genuinely unreachable without the operator manually scrolling and hunting for it.

**Note:** Root cause was not investigated (out of scope per agent rules — no source reading/diagnosis, no fix attempted). The observed pattern (works on hard navigation, not on SPA client-side navigation) is consistent with a scroll-to-hash effect that only runs on/after a full page load rather than on client-side route transitions, but this is offered only as a plausible shape for the developer, not a confirmed cause.

---

## Skipped Tests

### UT-10 — Missing/empty ledgers → honest empty state, no crash
**Verdict:** SKIPPED
**Reason:** This test's steps require renaming the live ledger files `runs/goal-session-mcp-loop/state/certified-claims.jsonl` and `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` to simulate a missing-ledger condition. The attempted `mv` command was denied by the Claude Code permission system's auto-mode classifier ("Modify Shared Resources": renaming live goal-session ledger files the QA agent did not create, mutating shared pipeline state beyond the browser-test task). Per agent policy, no attempt was made to route around the denial with an alternate mechanism (e.g. Python file I/O) — that would defeat the intent of the block. The ledger files were confirmed untouched immediately afterward (`certified-claims.jsonl` 7 rows, `staging-ledger.jsonl` 7 rows, both present). This specific error path (missing/empty ledger ⇒ empty payload, no crash) is listed in the phase spec's own Unit/integration TESTING REQUIREMENTS as covered by `apps/backend/tests/test_graveyard.py` fixtures — a browser-only agent cannot independently confirm that coverage; that verification belongs to the reviewer/auditor reading the test suite.

### UT-11 — Loading skeleton (8 bars) shown, then fully replaced
**Verdict:** SKIPPED
**Reason:** This test requires Chrome DevTools network throttling ("Slow 3G") to slow the fetch enough to observe the intermediate loading-skeleton frame. The Chrome MCP tool available in this environment (`mcp__plugin_superpowers-chrome_chrome__use_browser`) does not expose a network-conditions/throttle action (confirmed via its own `action:"help"` listing — no such action exists among navigate/click/type/extract/screenshot/eval/scroll/etc.), and page-level `eval` cannot invoke the CDP `Network.emulateNetworkConditions` domain method. The local backend responds in a few milliseconds and the tool's `navigate` action blocks until the page finishes loading, so the skeleton state (if present) cannot be reliably captured through any combination of actions available here. Per agent rules, this is reported as SKIPPED (tool limitation) rather than FAIL or an invented result.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-13
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-31-evidence/`
- **Ledger state used:** `certified-claims.jsonl` (7 rows, all FAIL), `staging-ledger.jsonl` (7 rows, all FAIL), `pre-registrations.jsonl` (11 rows) — all confirmed present and unmodified at both the start and end of this test run.
- **Backend restart note:** the backend process was intentionally stopped and restarted as part of UT-09 (expected/required by that test case). It was confirmed healthy (HTTP 200 on `/api/research/graveyard`) before and after the full test run. The frontend process was not touched.
