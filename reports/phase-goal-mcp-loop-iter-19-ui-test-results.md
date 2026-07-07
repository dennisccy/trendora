# Phase goal-mcp-loop-iter-19 — UI Test Results

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 23/24 tests passed (1 skipped)

All 14 P1 tests pass, including both headline fixes under test: the `/stocks` Sector-sort crash
(UT-01/02/03) and the `/data` backend OOM/prefill path (UT-12/13/14). The crash-containment
`error.tsx` boundary (UT-16/17) is confirmed working exactly as designed. The one SKIPPED test
(UT-18, P3) required a temporary edit to `app/layout.tsx` to force a root-layout throw — outside
this agent's "do not edit source files" rule — and was substituted with static code inspection
instead (see Skipped Tests section).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/stocks` loads on default null-heavy state | smoke | P1 | Heading/subtitle, table with Sector column, no "Backend unavailable", nav visible | Confirmed exactly: heading "Stocks", subtitle present, table renders 541/541 rows, Sector column shows Technology/Unassigned mix, sidebar nav intact | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-01-result.png` |
| UT-02 | Sort Sector ascending, no crash | happy-path | P1 | Table re-sorts, up-arrow indicator, no crash, nav visible | `aria-sort="ascending"` confirmed on Sector `<th>`, table re-ordered alphabetically (Communication Services→Industrials visible), no crash, nav fully intact | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-02-result.png` |
| UT-03 | Sort Sector descending, no crash | happy-path | P1 | Sort reverses, down-arrow, no crash, large Unassigned block near top | `aria-sort="descending"` confirmed, Utilities (3 rows) then large consecutive Unassigned block visible immediately after, no crash | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-03-result.png` |
| UT-04 | Sector filter lists "Unassigned" alphabetically | ux | P2 | "All sectors" first, remaining alphabetical, "Unassigned" between Technology/Utilities, never blank/"null" | DOM dump of all 11 `<option>`s confirms exact order: All sectors, Communication Services … Technology, **Unassigned**, Utilities | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-04-06-result.png` |
| UT-05 | Filter leaderboard by "Unassigned" | happy-path | P1 | Table narrows to Unassigned-only rows, count updates, no real-sector row visible | Count showed "422 / 541" (exact plan example); parsed tbody confirmed exactly 422 rows all "Unassigned", 0 rows with a real sector name | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-05-result.png` |
| UT-06 | No blank Sector cells | validation | P2 | Every row shows real sector or "Unassigned", never blank/"null" | Parsed ALL 541 rows (exceeds the 30-row sample asked for): 0 blank, 0 literal "null"; distribution Unassigned=422, Technology=57, Industrials=22, etc. | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-04-06-result.png` |
| UT-07 | Evidence badges present after sector fix | regression | P1 | All 3 scores/row show "Not yet proven" for first 10 rows | Verified first 10 rows (3×10=30 badges) AND, as a bonus, all 541 rows (1623 badges): 100% "Not yet proven", 0 `data-proven=true` | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-07-result.png` |
| UT-08 | Unmapped company shows "Unassigned" chip | happy-path | P1 | Chip reads "Unassigned" between setup badge and "as of" badge | On `/stocks/GL`: header card shows "Extended · Unassigned · as of 2026-07-01" exactly; page renders normally (chart, 3 scores) | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-08-result.png` |
| UT-09 | Mapped company (NVDA) unaffected | regression | P1 | Chip still reads "Technology" | `/stocks/NVDA` header card shows "Avoid · Technology · as of 2026-07-01"; unchanged, page normal | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-09-result.png` |
| UT-10 | Full-history chart renders post-rewrite | regression | P1 | Chart re-renders wider, "history since" reflects real deep date, Recent↔Full toggle both work, no error/blank | Full history: "3025 bars · history since 1999-01-22"; Recent: "1255 bars", same start date. Both directions render without error. **See UX Observation F1 below** re: the visual x-axis not extending fully to 1999 despite the caption/bar-count including that data | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-10-result.png`, `UT-10-recent.png` |
| UT-11 | Scanner run Sector column correct | happy-path | P2 | Every row real sector or "Unassigned", banner intact | Parsed all 541 rows of `/scanner-runs/410`: 0 blanks, identical distribution to `/stocks`; "Immutable snapshot — as of…" banner confirmed present | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-11-result.png` |
| UT-12 | Cold `/data` load, no hang/crash | smoke | P1 | Loads within ~20s, no "Backend unavailable", no crash | Loaded fully (~6s round-trip) with real numbers; no error card. **Caveat: this was a WARM load, not a true cold restart** — see note below | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-12-result.png` |
| UT-13 | `/data` coverage numbers stable cold vs warm | validation | P2 | Identical values across reload | Full "Dataset coverage" section text byte-identical between two consecutive loads (Price history, Universe, Candidate universe, Symbols, Trading days, Snapshot dates, Backfill gaps all matched) | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-13-result.png` |
| UT-14 | "Stale series" tile visible and readable | happy-path | P1 | Numeric count + definition text, not clipped | Tile shows count "1" and definition "Last bar more than 10 calendar days before the as-of — the series ended or halted…"; fully in frame in a targeted crop | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-14-result.png` |
| UT-15 | Membership timeline entries/exits (mid-history IPO) | happy-path | P1 | Ticker present on true accrual date, absent before, present on current leaderboard | DDOG entered 2020-08-03 ("+2 DDOG, NVDA"); confirmed absent from all of 2019 and 2020-01 through 2020-07 entries; DDOG found live on `/stocks` (rank #79, Technology) via search | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-15-entry-2020.png`, `UT-15-ddog-present.png` |
| UT-16 | Forced client error → contained `error.tsx` card | error | P1 | Card with warning icon + copy + Try again; nav preserved; not blank | Exact copy confirmed: "Something went wrong on this page" / full body text / "Try again" button; sidebar + header fully visible; all nav `href`s present in DOM even during the error state | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-16-result.png` |
| UT-17 | "Try again" recovers the page | happy-path | P2 | Error card disappears, leaderboard re-renders | After restoring `Array.prototype.sort` and clicking "Try again": error card gone, full 541/541 leaderboard re-rendered in default rank order | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-17-result.png` |
| UT-18 | Root-layout failure → `global-error.tsx` fallback | error | P3 | Nav-free standalone card with specific copy | NOT dynamically triggered (see Skipped Tests). Statically verified via source read: component renders its own bare `<html>/<body>`, deliberately imports no Sidebar/nav, copy matches exactly | SKIPPED | none (static source read only) |
| UT-19 | New copy has no anti-goal-#2 language | ux | P2 | No buy/sell/price-target/return-promise language in new copy | `error.tsx`/`global-error.tsx` copy and "Unassigned" label clean. **Extended scope:** full-source grep across `apps/frontend/app`, `components`, `lib` for buy/sell/guaranteed/price-target/will-rise/will-fall/invest/alpha-as-claim — zero violating hits (all "alpha" hits were CSS rgba opacity values; all "buy/sell" hits were code comments describing anti-goal-#2 compliance, not UI copy) | PASS | (source-level; no UI screenshot needed) |
| UT-20 | `/evidence` rows + regime label render | regression | P1 | Claim rows OR empty-state; regime badge readable, never blank/null | 7 claim rows render (not the empty state), each with FAIL badge, hypothesis tags, control comparison, registration date; "Breakout-watch setup" row shows "Regime: Risk-on" (clean, not blank/null) | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-20-21-evidence-result.png` |
| UT-21 | No "Proven"/PASS anywhere (all-FAIL preserved) | regression | P1 | Every status "Not yet proven"/"FAIL", never "PASS"/"Proven" | `/evidence`: 7/7 rows "FAIL", 0 "PASS". `/stocks`: 1623/1623 badges "Not yet proven" (541 rows × 3 scores). `/stocks/NVDA`: 3/3 "Not yet proven". Single "Proven" hit on `/evidence` was the subtitle's rule-explanation sentence, not a status | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-20-21-evidence-result.png` |
| UT-22 | Watchlist unknown-ticker error, no row added | error | P2 | Inline error, row count unchanged | Red inline "unknown ticker: ZZZZZ" message appeared; table still showed exactly 1 row (ABBV), "1 saved" unchanged | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-22-result.png` |
| UT-23 | Watchlist duplicate-ticker error, no 2nd row | error | P2 | Inline error, still exactly 1 row for that ticker | Red inline "ABBV is already on the watchlist" message appeared; table still showed exactly 1 ABBV row, never 2 | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-23-result.png` |
| UT-24 | Backtest as-of floor at 2005-02-25 | validation | P2 | No crash/blank; clamps or shows no-data; badge reflects real resolved date, never phantom | `?asof=1990-01-01` (genuinely before all price history): no crash, no blank page, no fabricated scorecard — the app silently degrades the unknown/out-of-range date to latest, strips the param, and "Viewing as-of 2026-07-01 (latest)" badge reflects the REAL resolved date. See note below on the actual floor mechanism | PASS | `reports/qa/goal-mcp-loop-iter-19-evidence/UT-24-result.png`, `UT-24-immediate-loading.png` |

---

## Passed Tests

### UT-01 — `/stocks` loads on default null-heavy state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-01-result.png`
- Heading "Stocks", subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason" both visible.
- Table columns: #, Ticker, Sector, Leadership, Entry Quality, Risk, Setup, Proximity to 52w high, 1D/5D/10D/20D/60D — all present.
- Row count "541 / 541"; no "Backend unavailable" card; sidebar nav fully visible.

### UT-02 — Sort `/stocks` leaderboard by Sector ascending — no crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-02-result.png`
- Clicked `button[aria-label="Sort by Sector"]`. Resulting DOM: `<th aria-sort="ascending">` and button re-labeled `aria-label="Sort by Sector, ascending"`.
- Table visibly re-sorted: Communication Services, Consumer Discretionary, Consumer Staples, Energy, Financials, Health Care, Industrials… — genuinely re-ordered, not a no-op.
- **This is the exact regression driver** (iter-18's uncaught `TypeError` on this click) — confirmed fixed, no crash, sidebar nav fully intact and clickable (all 11 nav `href`s present).

### UT-03 — Sort `/stocks` leaderboard by Sector descending — no crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-03-result.png`
- Second click on the same header: `<th aria-sort="descending">`, button re-labeled "Sort by Sector, descending".
- Order reversed: Utilities (NRG, VST, CEG) at top, immediately followed by a large consecutive block of "Unassigned" rows — exactly the visual sanity check the test plan describes. No crash.

### UT-04 — Sector filter dropdown lists "Unassigned" in the correct alphabetical position
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-04-06-result.png`
- Parsed all `<option>` elements of `select[aria-label="Filter by sector"]`: `All sectors, Communication Services, Consumer Discretionary, Consumer Staples, Energy, Financials, Health Care, Industrials, Technology, Unassigned, Utilities` — "Unassigned" sits exactly between Technology and Utilities; `value="Unassigned"` and its label text are both the plain word, never blank or literal `null`.

### UT-05 — Filter `/stocks` leaderboard by "Unassigned"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-05-result.png`
- Selected "Unassigned"; count indicator read "422 / 541" (matches the test plan's own example almost exactly).
- Parsed the filtered tbody: exactly 422 rows, 100% "Unassigned", 0 rows with any real sector name leaking through.

### UT-06 — No leaderboard row ever shows a blank Sector cell
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-04-06-result.png`
- Parsed the Sector `<td>` of all 541 rows (far exceeding the requested 30-row sample): 0 blank cells, 0 literal "null" strings. Distribution: Unassigned 422, Technology 57, Industrials 22, Consumer Discretionary 12, Financials 9, Health Care 7, Energy 4, Utilities 3, Communication Services 3, Consumer Staples 2 (sums to 541).

### UT-07 — Evidence status badges still present on every score after the sector fix
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-07-result.png`
- First 10 rows individually confirmed: 3/3 scores each show `data-proven="false"` + "Not yet proven".
- Extended to all 541 rows (1623 badges total): 100% "Not yet proven", 0 `data-proven="true"`, 0 non-standard status text.

### UT-08 — `/stocks/{ticker}` shows "Unassigned" for an unmapped company
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-08-result.png`
- Navigated to `/stocks/GL` (a confirmed Unassigned-sector name). Header card reads "Extended · Unassigned · as of 2026-07-01" in that exact position. Rest of page (Leadership/Entry Quality/Risk cards, chart, VCP pattern line) renders normally.

### UT-09 — `/stocks/{ticker}` unaffected for a mapped company — NVDA still "Technology"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-09-result.png`
- `/stocks/NVDA` header card reads "Avoid · Technology · as of 2026-07-01" — unchanged. Page renders normally with themes (AI Data Centre, Semiconductors, Megacap Leaders).

### UT-10 — `/stocks/{ticker}` Full-history chart still renders after the prefill rewrite
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-10-result.png` (Full history), `UT-10-recent.png` (Recent)
- On `/stocks/NVDA`, "Full history" is `aria-pressed="true"` by default on load, caption "3025 bars · as of 2026-07-01 · history since 1999-01-22 · older bars weekly-sampled". Clicked "Recent": caption changed to "1255 bars…" (same start date), chart re-rendered with a bounded ~4-year window, no error. Clicked back to "Full history": returned to "3025 bars", no error. Both directions render cleanly.
- **UX Observation (not a failure, see below) — "F1" carry item:** the chart's visible x-axis gridlines only label 2019–2026 in "Full history" mode even though the caption/bar-count include data back to 1999-01-22. The phase spec explicitly names this as "(Non-blocking carry — F1): confirm whether the Full-history chart plots pre-2018 weekly bars for >8y names… and widen the x-domain if not" — this browser check confirms the suspicion is real (the x-domain does not currently visually extend to the true first-bar date), but this is explicitly out of this iteration's Definition of Done, so it is reported as an observation, not a UT-10 failure. UT-10's own written pass bar ("wider date range extending back **toward** the history-since date," not necessarily all the way) is satisfied.

### UT-11 — `/scanner-runs/{runId}` Sector column shows correct labels, no blanks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-11-result.png`
- Opened `/scanner-runs/410` (2026-07-01 run). "Immutable snapshot — as of 2026-07-01" banner ("Stored exactly as scanned; never recomputed for today…") renders correctly. Parsed all 541 constituent rows: identical Sector distribution to `/stocks`, 0 blanks.

### UT-12 — Cold-started `/data` loads without hanging or crashing
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-12-result.png`
- **Caveat, per the test's own documented fallback:** the backend process (PID confirmed via `ps aux`, started by the goal-mode orchestration outside this agent's control) was already warm from earlier requests in this session; a genuine cold-restart was not attempted since restarting a shared backend process is outside a browser-qa-agent's remit and risked disrupting concurrent goal-mode infrastructure. The warm load completed fully (real numbers, no skeleton) well within the ~20s/60s budgets, with no "Backend unavailable" card and no crash. Separately, direct backend timing via `curl` on `/api/backtest` (a different, heavier endpoint) measured 31–35s for a fresh as-of computation — still no OOM/hang, just genuinely slower compute; noted as a UX observation, not a UT-12 failure (UT-12 is scoped to `/data`, which loaded fast).

### UT-13 — `/data` coverage numbers match between cold load and warm reload
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-13-result.png`
- Extracted the full "Dataset coverage" section's text on two consecutive loads: byte-identical, including "Universe (as of date) 541", "Candidate universe 122", "Symbols 587", "Trading days 5369", "Snapshot dates 410", "Backfill gaps 4959", and the "Gap range: 2005-02-28 → 2026-05-29" line.

### UT-14 — `/data` "Stale series" reason tile is visible and readable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-14-result.png`
- Cropped, zoomed capture of the "Universe resolution as of 2026-07-01" tile row confirms "Stale series" shows count "1" and definition text "Last bar more than 10 calendar days before the as-of — the series ended or halted, so the name exits membership (its months-old close can never misalign a relative-strength window)." — matches the expected phrasing almost verbatim, fully in frame.

### UT-15 — `/data` Dynamic-universe membership timeline shows correct entries/exits for a mid-history IPO name
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-15-entry-2020.png`, `UT-15-ddog-present.png`
- Selected Year=2020 in the timeline filter: row "2020-08-03" shows Entries "+2 DDOG, NVDA".
- Selected Year=2019: DDOG absent from all 8 rows (entries and exits) for the entire year. Also confirmed absent from 2020's earlier rows (05-01, 06-01, 07-01).
- Searched "DDOG" on `/stocks`: found at rank #79, Technology, Leadership 74.06 — a live, present member of today's universe. Absent-before/present-after its accrual is fully confirmed.

### UT-16 — Forced client-side error renders the contained `error.tsx` card with nav preserved
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-16-result.png`
- Monkeypatched `Array.prototype.sort` via DevTools-equivalent `eval`, then clicked "Sort by Ticker" to trigger the crash during React's render phase.
- Resulting card: warning-triangle icon, "Something went wrong on this page", "An unexpected error stopped this page from rendering. No data is lost — use the sidebar to open another page, or try this one again.", "Try again" button with circular-arrow icon — byte-exact match to `apps/frontend/app/error.tsx`'s source.
- Sidebar nav + top header remained visible; confirmed via DOM that all nav `<a href>`s (`/`, `/stocks`, `/themes`, `/sectors`, `/scanner-runs`, `/backtest`, `/research`, `/evidence`, `/watchlist`, `/methodology`, `/data`) were still present and real (not disabled) even while the error card was showing. Page did not go blank — this is the exact iter-18 failure mode, now fixed.

### UT-17 — "Try again" button on the error card attempts to recover the page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-17-result.png`
- Restored `Array.prototype.sort`, then clicked "Try again" (via XPath `//button[contains(., "Try again")]`) without reloading.
- Error card disappeared; the full Stocks leaderboard (541/541, default rank order) re-rendered successfully — a working table, not another error.

### UT-19 — New copy introduced this iteration contains no prohibited financial-advice language
**Verdict:** PASS
**Evidence:** source-level verification (no screenshot required)
- Read `error.tsx` and `global-error.tsx` source directly: all copy is limited to describing the technical failure and recovery option; no buy/sell/price-target/return-promise/alpha language.
- "Unassigned" reads as a neutral classification label everywhere it appears (dropdown, table cell, ticker-detail chip).
- **Extended beyond the narrow "new copy" scope** (per the dispatch note asking to complete the anti-goal-#2 sweep): ran a full-source grep across `apps/frontend/app`, `components`, `lib` for `buy|sell|should invest|guaranteed|will rise|will fall|price target|take profit|stop loss|risk-free`, capitalized `Buy`/`Sell` button-label patterns, `invest`, and `alpha` used as a claim word. Zero violations found; the only "buy/sell" hits were code comments explicitly documenting anti-goal-#2 compliance, and all "alpha" hits were CSS `rgba()` opacity parameters.

### UT-20 — `/evidence` renders claim rows/empty-state and regime labels correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-20-21-evidence-result.png`
- Heading "Evidence", subtitle "The certified-claims ledger — the single source of proven-ness…" both present; no "Backend unavailable".
- 7 claim rows render (leadership_score, Breakout-watch setup, ma_stack, vcp_contraction ×2, rs_spy_3m×high_proximity composite, rs_spy_3m top decile), each with a status badge, hypothesis tags, control comparison vs SPY, registration date "2026-07-03", forward-walk score-to-date.
- "Breakout-watch setup" row shows a second badge "Regime: Risk-on" — a recognizable, non-blank, non-null regime label.

### UT-21 — `/evidence` shows no "Proven"/PASS status anywhere
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-20-21-evidence-result.png`
- `/evidence`: 7/7 status badges read "FAIL", 0 read "PASS". The one non-"yet"-prefixed "Proven" text hit was the subtitle's rule-explanation sentence ("A signal reads 'Proven' ONLY when…"), not a status instance.
- `/stocks`: all 1623 evidence badges (541 rows × 3 scores) read "Not yet proven".
- `/stocks/NVDA`: all 3 score cards read "Not yet proven".
- Confirms the all-FAIL ledger state from the iter-17 sanctioned reset is honestly preserved, no stale "Proven" value leaked anywhere.

### UT-22 — Watchlist: adding an unknown ticker shows a clear inline error, no row added
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-22-result.png`
- Typed "ZZZZZ", clicked Add. Red inline message with warning-triangle icon: "unknown ticker: ZZZZZ". Table unchanged (still 1 row, ABBV; "1 saved" indicator unchanged).

### UT-23 — Watchlist: adding a duplicate ticker shows a clear inline error, no second row added
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-23-result.png`
- Typed "ABBV" (already saved), clicked Add. Red inline message: "ABBV is already on the watchlist". Table still shows exactly one ABBV row.

### UT-24 — Backtest: as-of date floor is enforced, no crash on an out-of-range date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-19-evidence/UT-24-result.png`, `UT-24-immediate-loading.png`
- Navigated to `/backtest?asof=1990-01-01` (confirmed via direct backend probe to be genuinely before all available price history — the backend's own `/api/backtest?as_of=1990-01-01` returns HTTP 400 "as_of 1990-01-01 is before the available price history"). No crash, no blank page at any point during load (skeleton → settled).
- Settled state: `window.location.href` shows the invalid `?asof` param was silently stripped; the page shows "Viewing as-of 2026-07-01 (latest)" — the real resolved date, not a phantom one; no fabricated 1990 scorecard was ever shown.
- **Mechanism note:** source inspection of `apps/frontend/components/asof-provider.tsx` clarifies the actual floor is data-driven, not the literal constant "2005-02-25": the provider validates any `?asof` value against the canonical `GET /api/runs` list of dates that actually have a stored snapshot, and degrades anything not in that list (too early, mid-gap, or malformed) straight to "latest," stripping the param — never fabricating, never crashing. Cross-checked `/api/runs`: the earliest entry is genuinely `2000-01-01`, with `2005-02-25` the second-earliest — close to, but not exactly, the phase spec's named figure (which turns out to describe the "Snapshots contributing" aggregate-evidence range's start, a descriptive stat, not a hard input-validation constant). The behavior itself — no crash, no fabrication, honest badge — is confirmed correct regardless of the exact figure's provenance.
- Also tested a malformed date (`as_of=not-a-date` directly against the backend): HTTP 422 with a clear message, consistent with the same no-crash, no-fabrication contract.

---

## Skipped Tests

### UT-18 — Root-layout failure renders the `global-error.tsx` fallback with no nav
**Verdict:** SKIPPED
**Reason:** The only way to trigger `global-error.tsx` is a genuine uncaught exception in the root layout itself (`app/layout.tsx`) or in `error.tsx` — this cannot be forced through navigation or a DevTools console injection (unlike UT-16's `Array.prototype.sort` trick, which worked because that crash happens inside an already-mounted client re-render). The test plan's own prescribed method is to temporarily add a `throw` to `app/layout.tsx`, reload, observe, then remove it. This agent's operating rules state "Do NOT edit source files" with no carve-out for temporary, self-reverting test probes, so the live dynamic trigger was not attempted.
**Substitute performed:** read `apps/frontend/app/global-error.tsx` directly. Confirmed it: (a) renders its own standalone `<html>/<body>` and deliberately imports no Sidebar/AsOfProvider/shared UI component (per its own code comment, exactly because those depend on the layout this boundary substitutes for) — so a nav-free fallback is what the code is built to produce; (b) its copy matches the test's expected text exactly: "Trendora hit an unexpected error" / "The application failed to render. No data is lost — reloading usually recovers; if it keeps happening, note what you were doing and report it." / "Try again" button. This is P3 (non-gating) and does not affect the overall verdict.

---

## Notes / Observations for the auditor

1. **UX Observation "F1" (non-blocking, phase-spec-acknowledged):** the `/stocks/{ticker}` Full-history chart's visible x-axis does not appear to widen all the way to a deep-history name's true first bar (e.g., NVDA's caption claims "history since 1999-01-22" and "3025 bars," but the rendered gridlines only label 2019–2026). The phase spec explicitly names this as a deferred, non-blocking item ("F1") to be confirmed — this browser check confirms the suspicion. UT-10 itself still passes because its own written bar only requires the range to widen "toward" the deep date, which it does (from a ~4-year bounded window to an ~8-year one).
2. **`/data` cold-load caveat:** UT-12/13 were run against an already-warm backend (the shared process serving this whole browser-QA session), not a freshly-restarted one, since restarting a backend process shared with the surrounding goal-mode orchestration was judged outside this agent's remit. The warm load result is still meaningful (no OOM, no hang, no crash, byte-identical repeat reads) but does not by itself certify the cold-path timing budget in `reports/perf-budgets.md` — that measurement is the developer/reviewer's responsibility per the phase spec.
3. **`/api/backtest` latency:** direct backend timing (`curl`) measured ~31–35s for a fresh as-of computation on `/api/backtest`. Not a crash or OOM, and not in scope for any single UT-XX pass/fail bar, but worth the auditor's awareness alongside the `/data` OOM fix, since it's the same broadened-basis compute-cost family.
4. **Chrome MCP capture timing:** several auto-captured screenshots/HTML dumps (on `click`/`navigate` actions) reflect the DOM at the instant of the action, before React finished re-rendering (observed on the NVDA chart toggle, the scanner-run detail page, and the Watchlist/Backtest async fetches). Each time this was suspected, a follow-up `screenshot`/`eval` action after the async work completed was used to confirm the real settled state before recording a verdict — none of the PASS verdicts above rely on a pre-settled capture.
5. **Screenshot evidence reuse:** `UT-01-result.png`/`UT-17-result.png` are intentionally byte-identical (both are the same real "default `/stocks`, 541/541" state — UT-17 landing back on it via "Try again" IS the expected pass condition). `UT-03-result.png` and `UT-04-06-result.png` are also byte-identical to each other because the Sector-descending sort from UT-03 was still active when the UT-04/06 filter-dropdown screenshot was taken (only the filter, not the sort, was touched in between) — this is a genuine, non-blank, correctly-labeled state, not a mislabeled/reused-blank-frame error; the underlying UT-04/06/07 verdicts are additionally backed by full structured DOM parsing (all 541 rows), not the screenshot alone.
6. **Golden replay scripts refreshed:** `J-01.json` (target journey, was stale — referenced a retired "120/120" dataset size and "Proven" text that contradicts the current honest all-FAIL state) and `J-04.json`/`J-05.json` (required-still-passing, `J-05` was stale — referenced "PASS" and old edge values `+6.36%`/`+6.12%` that no longer exist post the iter-17 sanctioned ledger reset) were all overwritten with values verified fresh this run. `J-10.json`, `J-11.json`, `J-12.json` were newly created (none existed before). All 6 lint clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (the test plan header said :8000; the operator note at dispatch corrected this to the actual running port, confirmed via `GET /api/health`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-07
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-19-evidence/`
- **Golden replay scripts:** `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-04,J-05,J-10,J-11,J-12}.json` (all lint-clean)
