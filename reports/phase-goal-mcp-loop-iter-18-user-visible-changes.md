# Phase goal-mcp-loop-iter-18 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-06
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On any stock's detail page (`/stocks/{ticker}`), users can toggle the price chart between "Recent" (a bounded ~5-year trailing window) and "Full history" (the stock's entire real price history back to its actual first trading day) by clicking a new segmented control next to the existing Regime toggle in the chart header.
- Users can read each chart's honest depth directly in the header caption — "N bars · as of DATE · history since FIRST_AVAILABLE_DATE" — e.g. AAPL/MSFT disclose "history since 1996-01-02," NVDA discloses "1999-01-22," and a post-IPO name (ARM/COIN/HOOD) honestly discloses its own short real history instead of implying decades of data. Switching to "Full history" on a long-tenured name appends "· older bars weekly-sampled" so users know deep bars are thinned, never fabricated.
- Users can add a much wider set of tickers to their watchlist (`/watchlist`) — any name in the broadened ~548-name candidate pool with real stored price bars is now accepted; previously only the ~122 originally-configured names could be added (a broadened-pool ticker used to be rejected with "unknown ticker").
- On `/data`, users can see WHY a stock exits the point-in-time universe due to stale data: a new "Stale series" reason card in the Universe Diagnostic panel names the exact threshold (10 calendar days) and explains that a name whose price feed stopped updating exits the scored universe rather than silently corrupting other stocks' relative-strength calculations.
- On `/methodology`, users can read the updated per-date membership rule, which now names the data-recency/staleness requirement alongside the existing history/price/volume gates.
- On `/stocks`, users see a much larger leaderboard reflecting the broadened ~548-name point-in-time candidate pool (previously capped near ~122 names).

---

## What Changed in the Visible UI

- The Stock Detail chart header (`/stocks/{ticker}`) gained a "Recent / Full history" segmented toggle and a depth-disclosure caption; switching ranges shows a loading skeleton while the new window fetches — the chart never shows a stale range mid-fetch.
- The `/data` page's Universe Diagnostic panel reason-card grid widened from 4 to 5 columns to fit the new "Stale series" card; the panel's hint text and the Coverage panel's "Admitted" metric definition were both reworded to mention the new freshness requirement.
- The `/data` page's Membership Timeline table column header changed from "Excl. hist / price / liq" to "Excl. hist / stale / price / liq," and each row's exclusion-count cell gained a fourth number.
- Every "Proven" evidence badge in the product now reads "Not yet proven" (or an honest FAIL state) — this affects the three score chips on every `/stocks` row, the three ScoreCards on every `/stocks/{ticker}` page, the Breakout-watch event-study row, and every factor/combination cohort on the Research lab pages. No score or edge anywhere in the product currently shows as backed by a passing evidence claim.
- The `/evidence` page now lists 7 regenerated claim rows, each dated 2026-07-03, each with a newly-computed (and uniformly failing) verdict, p-value, and holdout edge — none of the six previously-"Proven" values (e.g. +21.34%, +8.91%, p=0.0004998) or the retired 2026-06-30/07-01 register dates appear anywhere in the product any longer.
- The survivorship-bias disclosure text shown on `/backtest` and every `/research/*` lab page (factor lab, combination lab, regime lab, phase-severity lab, samples, severity-velocity) now describes "up to ~30 years of history (1996 to present)" instead of the previous shorter-window phrasing.
- `/stocks` (and its Sector column/filter) now includes rows for names outside the legacy ~122-symbol set; some of these newly-included names have no sector assigned (the sector map only covers the original ~122), so their Sector cell is expected to render blank rather than a fabricated label.

---

## What Old Behavior Changed

- **Chart range:** previously `/stocks/{ticker}` always requested and displayed the same bars for a given as-of date with no user control over span. Now the SAME endpoint accepts a `range` selection (Recent/Full history) and the default view is explicitly bounded to a trailing window — a long-tenured stock's full 30-year history is no longer shown by default; users must opt in via "Full history."
- **Watchlist ticker validation:** previously `POST /api/watchlist` rejected (404) any ticker outside the ~122 names in `config.universe.symbols`. Now it accepts any ticker in the broadened pool-loaded set or with real stored bars — a strictly larger set of tickers is addable; a genuinely unknown ticker still returns the same honest 404.
- **Chart ticker validation:** any stock-chart request for a broadened-pool ticker that used to 404 as "unknown ticker" now resolves successfully (same 404 behavior preserved for truly unknown tickers).
- **Evidence badges product-wide:** previously several scores/edges displayed "Proven" with specific historical numbers. All of those same surfaces now display "Not yet proven" / FAIL with newly-computed (all-failing) numbers, because the underlying evidence ledger was regenerated from scratch on the new 30-year data and none of the seven claims re-certified. This is a sanctioned, disclosed reset (a data-basis change), not an outage.
- **Backtest/Research survivorship caveat:** the wording changed (see above) — same location, same always-shown-banner behavior, different text.
- **Candidate-pool/member counts** shown in the `/data` Coverage panel ("Of N candidate names / M pool") are now much larger numbers than before (the pool grew from ~122 to ~548) — same display, bigger numbers.

---

## Not Visible Yet

- Per-series data vendor labels (now recorded in the regenerated `data/seed/meta.json`, e.g. which feed each symbol's bars came from) are not shown anywhere in the UI yet — deferred to a later iteration (J-14).
- The deep world-index and macro series carried in the new seed data (`_SPX`, `_NDX`, `_DJI`, `_VIX`, and FRED macro proxies) are loaded into the database but not wired into any chart, dashboard overlay, or `/data` display — surfacing them is explicitly out of scope this iteration (J-14 steps 2-3).
- Sector labels for the broadened-pool names (the ~400+ names added beyond the legacy ~122) are not yet populated — those stocks show without a sector wherever a sector is displayed (leaderboard column, detail page, sector filter) until a future iteration wires pool-wide sector mapping (J-13/J-14).
- The bounded snapshot-density policy (monthly cadence across most of the 30-year span, daily only for the most recent trading month, disclosed in the dev handoff) has no UI control or indicator of its own — it only shows up indirectly as which historical dates the Membership Timeline / Backtest can step through.
- `/data`'s Fetch/Expand-universe controls still describe the legacy ~122-name default (broadening that surface to the full 548-pool default is explicitly deferred to iter-19/J-13, not this iteration).
