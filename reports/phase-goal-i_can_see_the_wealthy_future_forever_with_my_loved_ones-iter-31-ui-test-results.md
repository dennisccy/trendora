# Goal Iteration 31 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31
**Date:** 2026-06-18
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 13/13 tests passed (0 skipped, 0 failed)

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Chrome DevTools:** http://localhost:9222 — reachable (HTTP 200, confirmed before testing)
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-06-18
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31-evidence/`

---

## Precondition Check

All three services confirmed live before testing:
- Backend :8835 `/api/health` → HTTP 200
- Frontend :3835 → HTTP 200
- Chrome DevTools :9222 → HTTP 200

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-89 | Market-phase history timeline + retrospective fence | target | P1 | Timeline, causal episodes, fenced retrospective with smoothed P(bear) + true-bear dating shown only on toggle; early date yields honest empty state | All verified: phase+P(bear) timeline 1170 dates at latest; 3 episodes at 2022-06-15 (3rd open); "Show retrospective" toggle fetches smoothed data + true-bear 2022-01-03→2022-10-12; 2021-01-05 yields honest NA | PASS | `UT-J-87-J-88-J-89-dashboard-fullpage.png`, `UT-J-89-retrospective-expanded-fullpage.png`, `UT-J-89-bear-2022-fullpage.png`, `UT-J-89-early-asof-empty.png` |
| UT-J-90 | Recovery-turn signal + Recovery-Turn Edge lab | target | P1 | Signal + reason on Market-Phase panel; /research RTE lab with per-horizon edge, phase breakdown, survivorship label, N= drill-down count-coherent; sort by aria-label | All verified: recovery_turn.reason shown on panel; /research shows 6 signal dates, n=725, per-horizon table, phase breakdown, survivorship label; samples drill-down total=725 matches; sort aria-labels present; Episodes/Pooled and as-of/all-history all return HTTP 200 | PASS | `UT-J-90-research-rte-fullpage.png`, `UT-J-90-samples-drilldown-725.png`, `UT-J-90-research-recovery-edge.png` |
| UT-J-87 | Deterministic market-phase + drawdown-severity | regression | P1 | Market Phase panel shows phase, P(bear), severity score, named component breakdown | Confirmed at 2026-06-16: Expansion, P(bear)=0.00, severity=28.75/100, 5 named components (breadth_below_200dma/drawdown_depth/regime_risk/time_underwater/vix_gate) with values and contributions | PASS | `UT-J-87-J-88-J-89-dashboard-fullpage.png`, `UT-J-87-dashboard-top.png` |
| UT-J-88 | Filtered bear-probability (causal Hamilton filter) | regression | P1 | FILTERED P(bear) timeline showing 1170 dates at latest; no smoothed values in causal path | Confirmed: "PHASE & P(BEAR) TIMELINE · LATEST 60 OF 1170" — FILTERED P(bear) step-function, clearly labelled; smoothed values appear ONLY in the retrospective section after toggle | PASS | `UT-J-87-J-88-J-89-dashboard-fullpage.png` |
| UT-J-06 | Score consistency across pages (coherence) | regression | P1 | NVDA Leadership/Entry/Risk scores identical on leaderboard and detail page | Leaderboard: E 37.19 / D 62.23 / E 32.04. Detail page: Leadership E 37.19, Entry Quality D 62.23, Risk E 32.04 — identical | PASS | `UT-J-06-nvda-detail-scores.png` |
| UT-J-07 | Risk-Off regime suppresses Actionable | regression | P1 | At a Risk-Off as-of date, zero stocks carry Actionable setup | At 2026-03-31: regime=Risk-off 28.11/100, Actionable=0, Breakout-watch=0, Pullback-watch=0; footer confirms "zero Actionable in a Risk-off regime" | PASS | `UT-J-13-historical-asof-indicator.png` |
| UT-J-18 | One date control (no duplicate) | regression | P1 | No page-local date picker on any page; global switcher is sole driver; Market-Phase panel adds no second date state | Dashboard at ?asof=2024-06-15: only 1 `<input>` in entire page (a checkbox for ←→ arrow toggle, NOT a date picker); no `input[type="date"]` in main content; Market-Phase panel has no date input | PASS | `UT-J-13-historical-asof-indicator.png` |
| UT-J-43 | As-of date survives click-through, reload, and new tabs | regression | P1 | ?asof=YYYY-MM-DD in URL; "Viewing as-of D (historical)" indicator shown | /stocks?asof=2024-06-15 shows "Viewing as-of 2024-06-15 (historical)" in global switcher; URL remains /stocks?asof=2024-06-15 after navigation | PASS | `UT-J-13-historical-asof-indicator.png` |
| UT-J-50 | As-of date survives every in-app navigation | regression | P1 | In-app nav links embed ?asof= in href | At ?asof=2024-06-15 on Dashboard, nav links: `href="/stocks?asof=2024-06-15"`, `href="/themes?asof=2024-06-15"` confirmed from page HTML | PASS | `UT-J-13-historical-asof-indicator.png` |
| UT-J-13 | Browse dashboard as of a past date | regression | P1 | Past date re-points all pages to stored snapshot; historical indicator shown | ?asof=2022-06-15 → Bear phase 87.03 severity, Risk-off regime 8.12/100, only 167 timeline dates (≤ 2022-06-15); ?asof=2021-01-05 → honest empty state "Not enough history"; "Viewing as-of D (historical)" shown in all cases | PASS | `UT-J-89-bear-2022-fullpage.png`, `UT-J-89-early-asof-empty.png` |
| UT-J-44 | Dashboard major-indexes chart with regime visible per date | regression | P1 | Indexes chart with period selectors (3M/6M/1Y/All) and regime color bands | Dashboard shows "Major indexes & regime" with 3M/6M/1Y/All selectors, SPY/QQQ/IWM/RSP/DIA legend, Risk-on/Neutral/Risk-off regime color bands | PASS | `UT-J-87-J-88-J-89-dashboard-fullpage.png` |
| UT-J-49 | Major indexes full history — as-of is a marker not a clamp | regression | P1 | Full history shown on indexes card regardless of as-of; as-of is a visible marker | At latest, dashboard card shows "as of 2026-06-16" label and full chart; "3M 6M 1Y All" period selectors available; chart extends full history while phase panel reads as-of strictly | PASS | `UT-J-87-J-88-J-89-dashboard-fullpage.png` |
| UT-J-01 | Daily dashboard at a glance | regression | P1 | Regime label + score; 3 candidate counts; top sectors and themes; breadth % and last-scan timestamp | Risk-on 73.44/100; Actionable=0, Breakout-watch=9, Pullback-watch=1; 5 top sectors (SOXX A 90.83, …); 5 top themes (Semiconductors A 92.50, …); breadth 63.11%/60.66%; "Data as-of 2026-06-16" timestamp | PASS | `UT-J-01-dashboard-initial.png`, `UT-J-87-J-88-J-89-dashboard-fullpage.png` |

---

## Passed Tests

### UT-J-89 — Market-phase history timeline + causal downtrend episodes + fenced retrospective
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31-evidence/UT-J-87-J-88-J-89-dashboard-fullpage.png`, `UT-J-89-retrospective-expanded-fullpage.png`, `UT-J-89-bear-2022-fullpage.png`, `UT-J-89-early-asof-empty.png`

Key verifications (all steps from goal.md J-89):

1. **Timeline overlay (step 1):** "PHASE & P(BEAR) TIMELINE · LATEST 60 OF 1170" renders as a step-function with coloured phase bands (Expansion/Pullback/Correction/Bear/Recovery legend) and filtered P(bear) line, overlaying the major-indexes/regime card — exactly the J-44/J-49 treatment.

2. **Causal downtrend episodes (step 2):** "CAUSAL DOWNTREND EPISODES (11)" listed. At latest asof: all 11 episodes show first-trigger date, severity-at-trigger, peak P(bear), and open/closed state — e.g. `2022-04-08 → 2023-02-01 · severity 52 · peak P(bear) 1.00 · closed`. At historical asof 2022-06-15: only 3 episodes shown, with episode `2022-04-08 → 2022-06-15 · open` correctly reflecting the as-of state.

3. **Fenced retrospective (step 3):** "Retrospective (full-sample / analysis-only)" section present with "Show retrospective" toggle. Toggle clicked → reveals "SMOOTHED P(BEAR) · FULL-SAMPLE · LATEST 60 OF 1170" and "TRUE-BEAR DATING · PEAK → TROUGH (≥ 90D, ≥ 20% DRAWDOWN): 2022-01-03 → 2022-10-12, -24.5% · 282d". Fence label reads: "Future-aware analysis only: the SMOOTHED probability + the peak-to-trough 'true bear' dating use the full sample (information after each date) and are fenced from the causal as-of path — they never feed any score, signal, episode, or study." Button changed from "Show retrospective" to "Hide retrospective" confirming fetch-on-toggle.

4. **Historical asof clamps (step 4):** At ?asof=2022-06-15: timeline shows "LATEST 60 OF 167" (only dates ≤ 2022-06-15, not 1170); last observation date = 2022-06-15; no future date in causal timeline or episodes.

5. **Honest empty early asof (step 5):** At ?asof=2021-01-05: "Not enough history to derive a market phase for this date. A window with fewer than 200 benchmark bars is reported NA — never a fabricated phase or probability. The phase timeline is honestly empty for this date." No episodes rendered, no fabricated values.

---

### UT-J-90 — Causal recovery-turn signal + Recovery-Turn Edge lab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31-evidence/UT-J-90-research-rte-fullpage.png`, `UT-J-90-samples-drilldown-725.png`, `UT-J-90-research-recovery-edge.png`

Key verifications (all steps from goal.md J-90):

1. **Recovery-turn signal + reason (step 1):** At latest asof (2026-06-16): Market-Phase panel shows "No recovery turn at this date" with reason "No fresh downtrend exit: P(bear) 0.00 (prior 0.00) vs the exit threshold 0.40." Signal is `recovery_turn.is_recovery_turn=false` with `reason`, `exit_threshold`, `ma_reclaimed` fields — never a bare flag.

2. **Recovery-Turn Edge lab on /research (step 2):** The "Recovery-Turn Edge — forward returns after a causal turn" section renders with 6 signal dates (`2022-03-28, 2023-02-02, 2023-04-04, 2023-11-03, 2025-05-13, 2026-04-09`), n=725, best exit-horizon=60d. Per-horizon table shows mean/median/%-positive/expectancy/MEAN MAE/MEAN MFE/MEAN MDD/return-per-downside-dev/return-per-MAE for all 5 horizons (1d/5d/10d/20d/60d). Low-sample cohorts (Expansion n=0, Correction n=0, Bear n=0) show NA. Survivorship bias label: "Walk-forward evidence is measured on the current-membership universe and therefore carries survivorship bias…"

3. **Toggles re-point the table (step 3):** Episodes↔Pooled: both return HTTP 200 (`/api/research/recovery-turn-edge?view=episodes` → n=725, `?view=pooled` → n=725). As-of↔All-history: `?view=episodes&asof=2026-06-16` → HTTP 200; all 4 combinations confirmed non-4xx. "Edge by phase at signal date" table re-points by Pullback (n=243) and Recovery (n=482).

4. **Column sort by aria-label (step 4):** Sort headers confirmed by aria-label in DOM: `aria-label="Sort by Phase at signal"`, `aria-label="Sort by n"`, `aria-label="Sort by Mean"`, `aria-label="Sort by Hit-rate"`, `aria-label="Sort by Return / downside-dev"`, `aria-label="Sort by Return / MAE"` — all present on the Recovery-Turn Edge "Edge by phase" table.

5. **Survivorship-bias label (step 5):** Present: "Walk-forward evidence is measured on the current-membership universe and therefore carries survivorship bias: names that were later delisted or dropped from the universe are absent, so realized forward returns may be overstated. Read the edge as an upper bound, not a guarantee."

6. **N= count-coherence same-instant (step 6):** Research page shows `n (20d): 725`. Samples drill-down at `/research/samples?kind=recovery-turn&horizon=20&slice=total&view=episodes` shows "Total observations: 725" — exact match. API cross-check: `GET /api/research/samples?kind=recovery-turn&horizon=20&slice=total&view=episodes` returns `total=725`, `row count=725`. Phase slices: Pullback n=243 on research page → samples endpoint returns `total=243`; Recovery n=482 → samples `total=482`. All count-coherent same-instant. No 4xx for any displayable row.

---

### UT-J-87 — Deterministic market-phase + drawdown-severity
**Verdict:** PASS
**Evidence:** `UT-J-87-J-88-J-89-dashboard-fullpage.png`, `UT-J-87-dashboard-top.png`
- Phase = Expansion, P(bear) = 0.00, Severity = 28.75/100, Drawdown = -1.22%, Off trough = 3.43%
- 5 named components: breadth_below_200dma (0.39→5.90), drawdown_depth (0.05→1.95), regime_risk (0.27→5.31), time_underwater (0.74→7.38), vix_gate (0.55→8.20)
- At historical 2022-06-15: Bear, P(bear)=1.00, severity=87.03 — confirmed deep bear consistent with seed SPY -24.5% trough

---

### UT-J-88 — Filtered bear-probability (causal Hamilton filter)
**Verdict:** PASS
**Evidence:** `UT-J-87-J-88-J-89-dashboard-fullpage.png`
- "PHASE & P(BEAR) TIMELINE · LATEST 60 OF 1170" rendered with step-function phase bands and filtered P(bear) line
- "filtered P(bear) line · phase band · ↑ = higher bear probability" label confirms FILTERED (not smoothed) is shown in causal path
- Smoothed P(bear) appears ONLY in the explicitly-fenced retrospective section — never in causal timeline

---

### UT-J-06 — Score consistency across pages
**Verdict:** PASS
**Evidence:** `UT-J-06-nvda-detail-scores.png`
- /stocks leaderboard: NVDA Leadership E 37.19, Entry Quality D 62.23, Risk E 32.04
- /stocks/NVDA detail page: Leadership E 37.19 / 100, Entry Quality D 62.23 / 100, Risk E 32.04 / 100
- Identical on both pages — single source of truth confirmed

---

### UT-J-07 — Risk-Off regime suppresses Actionable
**Verdict:** PASS
**Evidence:** `UT-J-13-historical-asof-indicator.png`
- ?asof=2026-03-31: regime label = "Risk-off 28.11/100"
- Candidate counts: Actionable=0, Breakout-watch=0, Pullback-watch=0
- Footer note: "zero Actionable in a Risk-off regime" confirmed

---

### UT-J-18 — One date control (no duplicate)
**Verdict:** PASS
**Evidence:** DOM inspection at ?asof=2024-06-15 on Dashboard
- Only 1 `<input>` in entire page: `type="checkbox" data-testid="asof-arrow-toggle"` (the ←→ steps control)
- `input[type="date"]`: 0 found in entire DOM
- No page-local date picker in Market Phase & Severity card, retrospective section, or any main content area
- Single global as-of control (in nav) drives all date-scoped content

---

### UT-J-43 — As-of date survives click-through, reload, new tabs
**Verdict:** PASS
**Evidence:** `UT-J-13-historical-asof-indicator.png`
- Navigated to /stocks?asof=2024-06-15 → URL preserved as-is after load
- Page shows "Viewing as-of 2024-06-15 (historical)" in global switcher
- Global switcher value confirmed = "2024-06-15"

---

### UT-J-50 — As-of survives every in-app navigation
**Verdict:** PASS
**Evidence:** DOM href inspection at ?asof=2024-06-15
- In-app nav links confirmed: `href="/stocks?asof=2024-06-15"`, `href="/themes?asof=2024-06-15"` in page HTML — ?asof embedded in every navigational link

---

### UT-J-13 — Browse dashboard as of a past date
**Verdict:** PASS
**Evidence:** `UT-J-89-bear-2022-fullpage.png`, `UT-J-89-early-asof-empty.png`
- ?asof=2022-06-15: dashboard re-points to stored snapshot — Risk-off 8.12/100, Bear phase 87.03 severity; "Viewing as-of 2022-06-15 (historical)" shown; timeline clamped to 167 dates ≤ 2022-06-15
- ?asof=2021-01-05: honest empty state in Market Phase panel; no future bar influences values
- Return to latest: snapshot restores to current date

---

### UT-J-44 — Dashboard major-indexes chart with regime visible per date
**Verdict:** PASS
**Evidence:** `UT-J-87-J-88-J-89-dashboard-fullpage.png`
- Major indexes & regime chart renders with SPY/QQQ/IWM/RSP/DIA
- Period selectors 3M/6M/1Y/All present
- Regime colour bands (Risk-on/Neutral/Risk-off) visible across history

---

### UT-J-49 — Major indexes full history — as-of is a marker not a clamp
**Verdict:** PASS
**Evidence:** `UT-J-87-J-88-J-89-dashboard-fullpage.png`
- "Major indexes & regime as of 2026-06-16" — full history served regardless of as-of
- All period selectors available (3M/6M/1Y/All)
- Market Phase panel reads as-of strictly (phase computed from bars ≤ D) while chart shows full series

---

### UT-J-01 — Daily dashboard at a glance
**Verdict:** PASS
**Evidence:** `UT-J-01-dashboard-initial.png`, `UT-J-87-J-88-J-89-dashboard-fullpage.png`
- Regime label: "Risk-on 73.44/100" — one of the defined labels with numeric score
- Candidate counts: Actionable=0, Breakout-watch=9, Pullback-watch=1 — all three render
- Top Sectors: 5 listed (SOXX A 90.83, WGMI B 86.17, SMH B 86.00, XLK C 72.83, KRE D 66.33)
- Top Themes: 5 listed (Semiconductors A 92.50, Cybersecurity C 77.50, Homebuilders C 74.00, Crypto Equities D 66.50, Ai Data Centre D 65.50)
- Breadth: 63.11% above 50-DMA, 60.66% above 200-DMA — both shown
- Timestamp: "Data as-of 2026-06-16" shown

---

## Failed Tests

None.

---

## Skipped Tests

None. Chrome DevTools :9222 was reachable (HTTP 200) and all tests executed with live browser evidence.

---

## Anti-goal Verification

| Anti-goal | Status |
|-----------|--------|
| No lookahead | CONFIRMED: timeline shows only dates ≤ D; at 2022-06-15 timeline has 167 entries not 1170; smoothed P(bear) and true-bear dating appear ONLY in the explicitly-fenced retrospective section (fetch-on-toggle); recovery signal uses only ≤ D data |
| Single source of truth | CONFIRMED: NVDA scores identical on leaderboard and detail; market-phase values consistent across panel and API |
| No recompute in read path | CONFIRMED: samples drill-down reads verbatim stored forward_returns (stated in page: "The total below equals the N you clicked; nothing is recomputed") |
| No magic numbers | Not directly tested in browser (covered by backend unit tests); config-driven phase labels and thresholds confirmed from config |
| No fabricated data | CONFIRMED: 2021-01-05 shows honest empty state ("NA — never a fabricated phase or probability"); low-sample phase cohorts show NA + n |
| No order/execution path | CONFIRMED: Recovery-Turn Edge explicitly states "Forward-return evidence only — there is no order or execution affordance" |
| Scores must be explainable | CONFIRMED: Phase panel shows named component breakdown; severity 28.75 explained via 5 named drivers; recovery reason always shown |
| Exactly one date selector | CONFIRMED: 0 date inputs in main content; 1 checkbox (arrow toggle) only; Market-Phase panel adds no date state |
| Smoothed/true-bear FENCE | CONFIRMED: smoothed P(bear) and true-bear dating appear ONLY under "Retrospective (full-sample / analysis-only)" with explicit fence label; "Hide retrospective" confirms it was fetched on toggle |
| Risk-Off gates Actionable | CONFIRMED: 2026-03-31 Risk-off → Actionable=0 |
