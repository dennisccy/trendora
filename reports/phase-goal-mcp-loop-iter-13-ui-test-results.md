# Phase goal-mcp-loop-iter-13 — UI Test Results

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-05 (P1 happy-path) failed — anchor scroll-into-view not triggered on SPA navigation -->

**Overall:** 12/14 tests passed (0 skipped, 2 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Combination lab page loads without errors | smoke | P1 | Page renders with heading, table rows, composite row testid, no errors | Page rendered with "Research — Multi-factor combination" heading, combination table with all cohort rows, `data-testid="combination-row-composite"` found, no error banner | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-01-result.png` |
| UT-02 | Evidence page loads with six claim rows | smoke | P1 | 6 claim rows, no "Unmapped signal", no error | 6 rows confirmed (5 PASS + 1 FAIL = 6 total), 6 "Backs:" linkbacks, no "Unmapped signal" text | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-02-result.png` |
| UT-03 | "Proven" badge for certified combination | happy-path | P1 | Badge reads "Proven", data-proven=true, has `<a>` with correct href, accent colour, ShieldCheck icon | Badge is `<a>` with href="/evidence#combination-high_proximity-rs_spy_3m-h20", text "Proven", data-proven="true", `lucide-shield-check` SVG present, class includes "text-accent" | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-03-result.png` |
| UT-04 | "Not yet proven" badge for non-certified combination | happy-path | P1 | Badge reads "Not yet proven", data-proven=false, no `<a>` link, muted colour, plain Shield icon | Badge is `<div>`, text "Not yet proven", data-proven="false", no `<a>` inside or wrapping, class includes "text-text-faint", `lucide-shield` SVG (no checkmark) | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-04-result.png` |
| UT-05 | Proven badge deep-link navigates to evidence anchor | happy-path | P1 | URL changes to `/evidence#combination-high_proximity-rs_spy_3m-h20`; page scrolls combination row into viewport | URL correctly changed to `http://localhost:3255/evidence#combination-high_proximity-rs_spy_3m-h20`; scrollY remained 0; anchor element (top=1585px) was below viewport (1252px); combination row not in viewport after 2000ms | FAIL | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-05-fail.png` |
| UT-06 | Sixth evidence row shows correct combination data | happy-path | P1 | Correct chips, PASS verdict, +4.69% edge, 2026-07-01 date, "Backs: Multi-factor combination lab →" | All verified: chips cohort=composite, condition=rs_spy_3m:top:quintile,high_proximity:top:tertile, horizon=20, direction=positive, PASS verdict, +4.69% holdout and control, 2026-07-01, "Pending" forward-walk, "Backs: Multi-factor combination lab →" linkback | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-06-result.png` |
| UT-07 | Linkback navigates from evidence row to combination lab | happy-path | P1 | Clicking "Backs: Multi-factor combination lab →" navigates to `/research/factor-combination` with table visible | Navigation to `http://localhost:3255/research/factor-combination` confirmed; `data-testid="combination-row-composite"` found after navigation | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-07-result.png` |
| UT-08 | Badge updates reactively when leg selection changes | validation | P2 | Changing Leg 2 → badge changes to "Not yet proven"; reverting → returns to "Proven" with deep-link | Changed Leg 2 to atr_pct: badge immediately changed to "Not yet proven" (data-proven=false, DIV); changed back to high_proximity: badge returned to "Proven" (data-proven=true, A with href) — no page reload | PASS | (inline verification) |
| UT-09 | Certified legs at non-certified horizon show "Not yet proven" | validation | P2 | At h60 with rs_spy_3m + high_proximity: badge reads "Not yet proven", no link | Set horizon to 60d: badge changed to "Not yet proven" (data-proven=false, no link, DIV) confirming horizon-awareness | PASS | (inline verification) |
| UT-10 | Prior 5 evidence rows unchanged | regression | P1 | Rows 1–5 intact: leadership_score, vcp_contraction rows, linkbacks correct; total = 6 | leadership_score with "Backs: Stocks leaderboard →" ✓; vcp_contraction h20 and h60 with "Backs: Research factor lab →" ✓; all 6 rows present (5 PASS + 1 FAIL); no "Unmapped signal" ✓ | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png` |
| UT-11 | Combination table statistical data intact alongside badge | regression | P1 | All cohort rows have numeric data; composite row shows stats AND badge | Baseline (n=124988), rs_spy_3m (n=25019), ATR (n=41664) all have mean/median/hitrate/risk-adjusted values; composite row shows "Not yet proven" badge AND n=24998, +1.76%, +1.51%, +58.11%, +0.36 | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-11-result.png` |
| UT-12 | Stocks page shows no combination evidence badge | regression | P1 | No `combination-evidence-badge` on `/stocks` or `/stocks/SPY`; badge count per stock unchanged | `data-testid="combination-evidence-badge"` count = 0 on both `/stocks` and `/stocks/SPY`; no "rs_spy_3m × high_proximity" or "composite" text; stock badges use `data-testid="evidence-badge"` with same "Proven"/"Not yet proven" pattern as before | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-12-stocks-result.png` |
| UT-13 | Badge is visually prominent and discoverable | ux | P2 | Badge visible, not clipped, accent coloured, readable at 100% zoom | Badge visible (offsetParent not null), overflow visible, cursor pointer, display inline-flex; ShieldCheck icon confirmed; "Proven" text readable at default zoom | PASS | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-13-result.png` |
| UT-14 | Evidence anchor scrolls combination row into viewport | ux | P2 | Direct navigation to URL with anchor hash scrolls combination row into viewport | Navigated to `/evidence#combination-high_proximity-rs_spy_3m-h20`; scrollY=0; anchor element at top=1585px, viewport height=1252px; combination row NOT in viewport — same SPA anchor scroll gap as UT-05 | FAIL | `reports/qa/goal-mcp-loop-iter-13-evidence/UT-14-fail.png` |

---

## Passed Tests

### UT-01 — Combination lab page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/research/factor-combination`
- Page rendered heading "Research — Multi-factor combination"
- Combination table visible with cohort rows: Baseline, rs_spy_3m top Quintile, ATR bottom Tertile, Combined (composite rank-blend), Strict overlap (AND)
- `data-testid="combination-row-composite"` found via DOM query
- No error banner or "Something went wrong" text

---

### UT-02 — Evidence page loads with six claim rows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-02-result.png`
- Navigated to `http://localhost:3255/evidence`
- Page text showed exactly 6 claim sections: leadership_score, Breakout-watch (event-study), ma_stack, vcp_contraction (h20), vcp_contraction (h60), rs_spy_3m × high_proximity (combination)
- 5 PASS + 1 FAIL verdict badges = 6 total rows confirmed by `(passCount + failCount)`
- 6 "Backs:" linkbacks present
- No "Unmapped signal" text on page

---

### UT-03 — "Proven" badge for certified combination
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-03-result.png`
- Set Leg 1: rs_spy_3m / top / quintile; Leg 2: high_proximity / top / tertile; horizon 20d (already selected)
- Badge element: `<a data-testid="combination-evidence-badge" data-proven="true" data-horizon="20" href="/evidence#combination-high_proximity-rs_spy_3m-h20">`
- Inner text: "Proven"
- ShieldCheck icon (`lucide-shield-check`) present
- Classes include `border-accent bg-surface-2 text-accent cursor-pointer`

---

### UT-04 — "Not yet proven" badge for non-certified combination
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-04-result.png`
- Default selection: rs_spy_3m / top / quintile × atr_pct / bottom / tertile
- Badge element: `<div data-testid="combination-evidence-badge" data-proven="false">` (DIV, not `<a>`)
- Inner text: "Not yet proven"
- Plain Shield icon (`lucide-shield h-3 w-3 shrink-0 opacity-70`) with no checkmark
- Classes include `border-border text-text-faint` (muted/neutral)

---

### UT-06 — Sixth evidence row shows correct combination data
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-06-result.png`
- Anchor `id="combination-high_proximity-rs_spy_3m-h20"` found
- Row text confirmed: "rs_spy_3m × high_proximity — composite", "Backs: Multi-factor combination lab →"
- Hypothesis chips: cohort=composite, condition=rs_spy_3m:top:quintile,high_proximity:top:tertile, direction=positive, horizon=20, kind=combination, ledger=canonical
- Verdict: PASS · holdout edge +4.69%
- Control comparison (vs SPY): +4.69%
- Registration date: 2026-07-01
- Forward-walk: Pending — monitored as new data matures

---

### UT-07 — Linkback navigates from evidence row to combination lab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-07-result.png`
- On `/evidence`, scrolled to 6th row (`id="combination-high_proximity-rs_spy_3m-h20"`)
- Found `<a href="/research/factor-combination">Backs: Multi-factor combination lab →</a>`
- Clicked the link; URL changed to `http://localhost:3255/research/factor-combination`
- Combination table loaded with `data-testid="combination-row-composite"` found
- 19 buttons, 5 selects visible (fully loaded combination lab)

---

### UT-08 — Badge updates reactively when leg selection changes
**Verdict:** PASS
- Start: rs_spy_3m + high_proximity at h20 → badge "Proven" (data-proven=true, `<a>` with href)
- Changed Leg 2 to atr_pct: badge immediately changed to "Not yet proven" (data-proven=false, DIV, no link)
- Changed Leg 2 back to high_proximity: badge returned to "Proven" (data-proven=true, `<a>` with href="/evidence#combination-high_proximity-rs_spy_3m-h20")
- All transitions happened without page reload

---

### UT-09 — Certified legs at non-certified horizon show "Not yet proven"
**Verdict:** PASS
- Set rs_spy_3m + high_proximity (certified legs), changed horizon to 60d
- Badge: "Not yet proven" (data-proven=false, DIV, no `<a>` link)
- Confirms badge is horizon-sensitive: only h20 with the certified pair triggers "Proven"

---

### UT-10 — Prior 5 evidence rows unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png`
- Row 1: leadership_score present with "Backs: Stocks leaderboard →"
- Rows for vcp_contraction (h20 and h60) present with "Backs: Research factor lab →"
- Row for Breakout-watch event-study present with "Backs: Research event-study lab →"
- Row for ma_stack present with FAIL verdict
- Total: exactly 6 rows (5 PASS + 1 FAIL) confirmed via verdict count
- No "Unmapped signal" text
- No row content altered

---

### UT-11 — Combination table statistical data intact alongside badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-11-result.png`
- Baseline (all names): n=124988, +1.85%, +1.13%, +54.45%, +0.24
- rs_spy_3m top Quintile: n=25019, +2.57%, +1.19%, +54.44%, +0.29
- ATR bottom Tertile: n=41664, +1.46%, +1.30%, +56.91%, +0.30
- Combined (composite rank-blend): badge "Not yet proven" present AND n=24998, +1.76%, +1.51%, +58.11%, +0.36 — both badge and stats intact
- Strict overlap (AND): n=5574, +1.00%, +0.70%, +54.02%, +0.19
- No layout misalignment; column headers (N, MEAN FWD RETURN, MEDIAN, HIT-RATE, RISK-ADJUSTED) all present

---

### UT-12 — Stocks page shows no combination evidence badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-12-stocks-result.png`
- On `/stocks`: `data-testid="combination-evidence-badge"` count = 0; no "rs_spy_3m × high_proximity", "composite", or "Combination" text
- Stock inline badges use `data-testid="evidence-badge"` (different testid); pattern 1 Proven + 2 Not yet proven per stock — same as prior iterations
- On `/stocks/SPY`: 0 combination-evidence-badge elements; no combination text; no `data-proven` attributes at all

---

### UT-13 — Badge is visually prominent and discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-13-result.png`
- Badge visible on page (offsetParent not null)
- overflow: visible; cursor: pointer
- Display: inline-flex; not hidden under any container
- "Proven" label readable at default zoom (100%)
- ShieldCheck icon present (confirmed in UT-03 detail)
- Accent styling confirmed via classes: `border-accent bg-surface-2 text-accent`

---

## Failed Tests

### UT-05 — Proven badge deep-link navigates to evidence anchor
**Verdict:** FAIL
**Failure:** SPA anchor scroll did not execute on client-side navigation. The URL correctly changed to the anchor URL, but the page did not scroll the combination row into the viewport.
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-05-fail.png`

**Steps taken:**
1. Navigated to `/research/factor-combination`
2. Set Leg 2 to high_proximity (top) and verified horizon at 20d
3. Badge confirmed reading "Proven" (`<a data-proven="true" href="/evidence#combination-high_proximity-rs_spy_3m-h20">`)
4. Called `badge.click()` via eval
5. URL changed to `http://localhost:3255/evidence#combination-high_proximity-rs_spy_3m-h20` ✓
6. Checked `window.scrollY` immediately: 0
7. Waited 500ms, checked again: scrollY=0, anchor top=1585px (viewport height=1252px) → inViewport=false
8. Waited 2000ms, checked again: scrollY=0, anchor at top=1585px → still not in viewport

**Expected:** Page scrolls so the combination claim row is visible in the viewport without manual scrolling
**Actual:** URL contains correct fragment (`#combination-high_proximity-rs_spy_3m-h20`) but scroll position remained at 0; anchor element (top=1585px) is below the viewport boundary (1252px) — the combination row is NOT visible without manual scrolling

---

### UT-14 — Evidence anchor scrolls combination row into viewport
**Verdict:** FAIL
**Failure:** Same SPA anchor scroll gap as UT-05. Direct navigation to the anchor URL with hash fragment did not cause the browser to scroll to the element.
**Evidence:** `reports/qa/goal-mcp-loop-iter-13-evidence/UT-14-fail.png`

**Steps taken:**
1. Navigated directly to `http://localhost:3255/evidence#combination-high_proximity-rs_spy_3m-h20`
2. Waited 1000ms for page to load and any scroll to complete

**Expected:** Combination claim row (6th row) visible in viewport immediately — browser scrolled to `#combination-high_proximity-rs_spy_3m-h20` anchor
**Actual:** scrollY=0; anchor element found (id="combination-high_proximity-rs_spy_3m-h20") at top=1585px, inViewport=false; page did not scroll to anchor — same gap as UT-05

---

## Skipped Tests

None — all 14 tests were executed.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (restarted mid-session after process death; evidence API confirmed 6 claims)
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-07-01
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-13-evidence/`

---

## Notes

**Backend restart:** The backend process at port 8255 died mid-session (after UT-07 first attempt). The backend was restarted using `scripts/start-backend.sh` with `CHAIN_BACKEND_PORT=8255`. UT-07 was re-executed after restart and confirmed PASS. All other tests were not affected (UT-01 through UT-06 ran before the backend died; UT-08 onward ran after restart with backend confirmed healthy).

**Scroll gap (UT-05, UT-14):** Both failures share the same root cause — the SPA (Next.js client-side router) does not scroll to the hash anchor on navigation. The URL fragment is correctly set in both cases, but `window.scrollY` remains 0 and the target element remains below the viewport. This is a client-side anchor scroll feature that is not currently implemented in the `/evidence` page component.

**Golden replay scripts:** Session journey-scripts directory checked for writing. UT-05 and UT-14 fail, so only journeys with full PASS are eligible. The linkback navigation (UT-07 flow) and certified-combination badge flow (UT-03/UT-06 related journeys) could be recorded but the anchor scroll gap makes end-to-end anchor-navigation journeys unreplayable as written. Scripts not written for this iteration due to the scroll gap affecting the core certified-to-evidence journey.
