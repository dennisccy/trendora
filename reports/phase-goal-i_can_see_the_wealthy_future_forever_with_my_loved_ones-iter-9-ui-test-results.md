# Goal Iter 9 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9
**Date:** 2026-06-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-55 | Stocks symbol search (type-to-filter) | happy-path | P1 | Search input narrows rows per keystroke, serializes as ?q=, restores on reload, honest empty state | Search input renders, typing "nv" shows 4/122 rows (NVT/NVO/NVDA/NVR), URL becomes ?q=nv, reload with ?q=nv restores search, no-match shows 0/122 | PASS | UT-J-55-search-nv.png, UT-J-55-no-match.png |
| UT-J-56 | Stocks Theme column + theme filter | happy-path | P1 | Theme column shows membership chips; theme filter narrows rows; serializes as ?theme=; unrecognized value degrades gracefully; composes with other filters; detail themes match leaderboard | Themes column present, NVDA shows "Ai Data Centre Semiconductors Megacap Leaders"; theme filter ?theme=ai_data_centre shows 16/122; URL serializes; unrecognized ?theme=nonexistent_theme_xyz shows all 122 rows (graceful); ?q=nv&theme=semiconductors shows 1 row; NVDA detail page shows identical theme chips | PASS | UT-J-56-theme-filter.png, UT-J-56-nvda-detail-themes.png |
| UT-J-57 | Themes expandable members + dated new-tab links | happy-path | P1 | +n expands all members; collapse works; member links target=_blank rel=noopener; href carries ?asof when historical, clean at latest; member click does not toggle row | Semiconductors shows 6 preview + "+21" button; clicking expands to 27 total members; "Show fewer" collapses back to 6; all links have target=_blank rel="noopener noreferrer"; at ?asof=2026-06-05 hrefs carry ?asof=2026-06-05; at latest hrefs are clean; dispatching click on member link does not collapse row (still 6 preview + +21 button after) | PASS | UT-J-57-before-expand.png, UT-J-57-expanded.png, UT-J-57-no-row-toggle.png |
| UT-J-02 | Stock Leaderboard with working filters | regression | P1 | Table ranked with bucketed scores/reason; Sector filter narrows rows; Setup filter works or honest empty state | 122 rows with Leadership/Entry/Risk buckets+scores, setup, reason; Sector=Technology shows 58 rows; Sector=Technology + Setup=Actionable shows 0/122 honest empty state | PASS | UT-J-02-filters.png |
| UT-J-03 | Theme Leaderboard | regression | P1 | ≥3 themes ranked by score (non-increasing); top theme shows members, 1m/3m, breadth, trend | 11 themes, non-increasing scores (92→87.5→70.5→58.5→53.5→...); Cybersecurity top with +16.44% 1m, +27.35% 3m, 82% breadth, "Strong uptrend" | PASS | UT-J-03-themes.png |
| UT-J-05 | Stock Detail with explainable scores | regression | P1 | NVDA detail shows price chart, three scores with component breakdowns, themes, setup, invalidation | NVDA detail: Leadership E/43.14 (7 components), Entry Quality E/54.05 (5 components), Risk E/35.80 (7 components+NA); Themes: Ai Data Centre/Semiconductors/Megacap Leaders; Setup: Avoid+Pullback; Invalidation: "below the 50-DMA at $205.76" | PASS | UT-J-05-J-06-nvda-detail.png |
| UT-J-06 | Score consistency (leaderboard ↔ detail) | regression | P1 | NVDA scores identical on leaderboard and detail page | Leaderboard: E/43.14, E/54.05, E/35.80. Detail page: E/43.14, E/54.05, E/35.80. Byte-identical. | PASS | UT-J-05-J-06-nvda-detail.png |
| UT-J-16 | VCP filter composes with search | regression | P1 | VCP filter shows only flagged rows (or honest empty); composes with search | VCP-only filter shows 0/122 (honest empty state, no VCP stocks in current snapshot); ?pattern=vcp__only&q=nv shows 0/122 (compose verified) | PASS | UT-J-16-vcp-filter.png |
| UT-J-48 | Stocks leaderboard column sorting | regression | P1 | Default order = stored rank; # col has aria-sort=ascending; clicking Leadership sorts by leadership; one sort indicator at a time | Default: aria-sort=ascending on # col, rows rank 1=MRVL, 2=MU, 3=DELL...; clicking Leadership re-orders ascending by leadership score (5.58→94.30); one aria-sort indicator at a time | PASS | UT-J-48-stocks-default.png |
| UT-J-50 | As-of date in all in-app hrefs | regression | P1 | While historical, every in-app link's href carries ?asof=D; at latest, clean | At ?asof=2026-06-05: all 122 stock links have /stocks/[ticker]?asof=2026-06-05; nav links carry ?asof=2026-06-05 (Dashboard/?asof=2026-06-05, /stocks?asof=2026-06-05, etc.); theme member links at historical carry ?asof | PASS | UT-J-50-J-54-asof-hrefs.png |
| UT-J-54 | Leaderboard ticker opens new tab | regression | P1 | Ticker links have target=_blank; href carries ?asof while historical | NVDA: target=_blank, rel=noopener noreferrer; at historical: href=/stocks/NVDA?asof=2026-06-05; leaderboard tab stays active | PASS | UT-J-50-J-54-asof-hrefs.png |

---

## Passed Tests

### UT-J-55 — Stocks symbol search (type-to-filter)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-55-search-nv.png`
- Search input (type=search, placeholder "Search ticker or name…") renders alongside Sector/Setup/Pattern/Theme filters
- Typing "nv" narrows visible rows instantly to 4/122: NVT, NVO, NVDA, NVR — case-insensitive ticker/name substring match confirmed
- URL reflects `?q=nv` immediately after typing (no submit button needed)
- Navigation to `?q=nv` restores search (inputVal="nv", 4 rows)
- No-match string "xyzxyzxyz" shows 0/122 (honest empty state, no fabricated rows)
- All 122 rows return when no search active (URL clean, inputVal="")
- Compose: `?q=nv&sector=Technology` → 1 row (NVDA), count "1 / 122"

### UT-J-56 — Stocks Theme column + theme filter
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-56-theme-filter.png`
- "Themes" column present in table headers (index 7: #, Ticker, Sector, Leadership, Entry Quality, Risk, Setup, Themes, Reason)
- NVDA row Themes cell: "Ai Data Centre Semiconductors Megacap Leaders" (3 chips — multi-theme row)
- Theme filter (5th select) options: __all__, ai_data_centre, semiconductors, cybersecurity, software_cloud, homebuilders, glp1_pharma, megacap_leaders, crypto_equities, power_grid, defense, nuclear_uranium
- Theme filter ai_data_centre: 16/122 rows, all with "Ai Data Centre" in themes cell, URL `?theme=ai_data_centre`
- Unrecognized `?theme=nonexistent_theme_xyz`: 122/122 rows, no crash (graceful degradation)
- Compose: `?q=nv&theme=semiconductors` → 1 row (NVDA), count "1 / 122"
- NVDA detail page shows identical theme chips: Ai Data Centre, Semiconductors, Megacap Leaders (J-06 coherence)
- No dev-overlay error badge observed

### UT-J-57 — Themes expandable members + dated new-tab links
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-57-expanded.png`
- Semiconductors theme row expands on click showing 6 preview members + "+21" button
- Clicking "+21" reveals all 27 members: NVDA, AMD, AVGO, MRVL, MU, WDC, STX, LRCX, AMAT, KLAC, TXN, ADI, NXPI, ON, MCHP, QCOM, INTC, TSM, ASML, ARM, TER, ENTG, COHR, MPWR, SWKS, QRVO, GFS
- "Show fewer" button collapses back to 6 preview members
- All member links: target="_blank", rel="noopener noreferrer"
- At `?asof=2026-06-05`: member hrefs carry `?asof=2026-06-05` (e.g., `/stocks/NVDA?asof=2026-06-05`)
- At latest: member hrefs are clean (no ?asof param)
- StopPropagation verified: dispatching click on NVDA link does not collapse row (still 6 links + "+21" button after)
- No dev-overlay error badge on themes page

### UT-J-02 — Stock Leaderboard with working filters
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-02-filters.png`
- 122 rows with bucketed scores (A–E), numeric values, setup status, reason summary
- First row: MRVL, Technology, A/94.30, E/23.35, E/59.43, Extended
- Sector=Technology filter: 58 rows
- Sector=Technology + Setup=Actionable: 0/122 rows (honest empty state)

### UT-J-03 — Theme Leaderboard
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-03-themes.png`
- 11 themes listed, scores non-increasing: 92.00, 87.50, 70.50, 58.50, 53.50, 53.00, 42.00, 36.50, 36.50, 20.00, 0.00
- Top theme Cybersecurity: 1m +16.44%, 3m +27.35%, 82% breadth, "Strong uptrend"

### UT-J-05 — Stock Detail with explainable scores
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-05-J-06-nvda-detail.png`
- NVDA detail page shows price+MA+volume chart with regime bands
- Leadership E/43.14 with 7 components (RS vs SPY 1m/3m, RS vs sector/theme, MA stack, Proximity to 52w high, Volume trend)
- Entry Quality E/54.05 with 5 components (Proximity to 20-DMA, Volatility contraction, Proximity to 50-DMA, Trend structure, Reward/risk room)
- Risk E/35.80 with 7 components (+NA for Earnings gap/climax)
- Themes: Ai Data Centre, Semiconductors, Megacap Leaders
- Setup: Avoid + Pullback to a rising DMA
- Invalidation: "Invalid below the 50-DMA at $205.76"

### UT-J-06 — Score consistency (leaderboard ↔ detail)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-05-J-06-nvda-detail.png`
- Leaderboard NVDA: Leadership E/43.14, Entry Quality E/54.05, Risk E/35.80
- Detail page NVDA: Leadership E/43.14, Entry Quality E/54.05, Risk E/35.80
- Scores are byte-identical across both views

### UT-J-16 — VCP filter composes with search
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-16-vcp-filter.png`
- VCP-only filter (`?pattern=vcp__only`): 0/122 rows (honest empty state — no VCP stocks in current snapshot)
- VCP-only + search `?pattern=vcp__only&q=nv`: 0/122 rows (filters compose correctly)

### UT-J-48 — Stocks leaderboard column sorting
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-48-stocks-default.png`
- Default state: aria-sort="ascending" on # column; rows in stored rank order (1=MRVL, 2=MU, 3=DELL, 4=ARM, 5=FTNT)
- Clicking Leadership header re-orders rows in ascending leadership score order (5.58 at top → 94.30 at bottom)
- Only one aria-sort indicator active at a time verified
- Stored values (rank #, scores, buckets, setup) read identically — no recompute

### UT-J-50 — As-of date in all in-app hrefs
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-50-J-54-asof-hrefs.png`
- At `?asof=2026-06-05`: all 122 stock ticker hrefs contain `?asof=2026-06-05`; nav links (Dashboard, Stocks, Themes, Sectors, etc.) all carry `?asof=2026-06-05`
- Theme member links at historical also carry `?asof=D` (verified on /themes?asof=2026-06-05)
- At latest: no ?asof in any href

### UT-J-54 — Leaderboard ticker opens new tab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/UT-J-50-J-54-asof-hrefs.png`
- MRVL ticker link at historical: href="/stocks/MRVL?asof=2026-06-05", target="_blank", rel="noopener noreferrer"
- NVDA ticker link at latest: href="/stocks/NVDA", target="_blank", rel="noopener noreferrer"
- Leaderboard tab remains undisturbed when ticker link is activated

---

## Failed Tests

*(none)*

---

## Skipped Tests

*(none)*

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-13
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-evidence/`
