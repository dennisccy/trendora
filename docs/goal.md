# Project Goal

> This goal drives the **decision-quality improvement loop** for Trendora. The original
> feature-complete product goal (GOAL_ACHIEVED) is archived at [`docs/goal-product.md`](goal-product.md)
> and remains the description of the underlying product. This file evolves Trendora from
> *"ranks the market with explainable scores"* to *"ranks the market AND proves, out-of-sample,
> which of its signals actually work — showing an honest evidence status on everything."*

## Vision

Trendora already produces explainable, regime-aware equity-leadership rankings (three independent
scores — Leadership, Entry Quality, Risk — plus market regime/phase and realized forward-return
evidence). The next evolution makes every signal **provable, not just explainable**: each score,
ranking, and "edge" the user sees carries a visible **evidence status** sourced from an append-only
**evidence ledger** of out-of-sample, control-beating, multiple-testing-corrected claims. Unvalidated
signals are shown as *"not yet proven"* — never as confident numbers. The platform improves itself by
mining its own data for candidate decision-support views and shipping only the ones a statistical
**referee** certifies. This is research-only decision support; it never predicts returns or places orders.

## Target Users

Self-directed, quant-minded swing/position traders who distrust black-box signals and want **hard,
out-of-sample evidence** before risking capital — now served not just explainable scores but provable
ones, with honest "this isn't proven yet" markers when the evidence is thin or fails.

## Success Criteria

- Every user-facing score / ranking / edge carries a **visible, accurate evidence status** ("proven" or
  "not yet proven") sourced from the evidence ledger — never a confident number without a status.
- A user can **audit the proof** behind any "proven" claim: the out-of-sample test, the control
  comparison (vs SPY / QQQ / sector ETF / random same-sector), and the certified-claim id + date.
- Failed or unvalidated signals are **explicitly flagged** as not proven, never shown as confident.
- Each successful iteration ships **at least one referee-certified** decision-support improvement, and
  **zero uncertified edges** reach the UI.
- Displayed numbers are **correct** (match the engine's computation for the same as-of date), not just
  rendered.

## Key Capabilities

1. **Evidence badges + drill-down** on every score/ranking surface — a "Proven / Not yet proven" badge
   inline, expanding to the backing out-of-sample test, controls, and certified-claim id/date.
2. **Evidence ledger surface** — an auditable list of certified claims (hypothesis, out-of-sample
   verdict, control comparison, registration date, forward-walk score-to-date).
3. **Regime-conditioned evidence** — decision-support conditioned on the current regime/phase, showing
   the out-of-sample evidence for *that* regime, labeled with the regime it applies to.
4. **Honest uncertainty / noise marking** — when evidence is thin or a pattern fails out-of-sample, the
   UI says so plainly instead of presenting a confident-looking number.
5. **Self-improving evidence loop** (internal) — each iteration proposes a decision-support improvement
   from the platform's own data and ships only referee-certified ones (enforced by the post-decompose gate).

## Non-Goals

- No return/price prediction, "buy/sell" signals, price targets, or alpha claims. Decision support only.
- No order placement, broker keys, or trade simulation.
- Not a rewrite — the evidence layer is **additive** to the existing surfaces (Dashboard, Stocks,
  Sectors, Themes, Backtest, Research labs, Data, Watchlist).

## Constraints

- Local-first, deterministic, offline against the committed seed; **strict no-lookahead** preserved
  (scoring uses bars ≤ as-of; forward returns use bars > as-of).
- **All "proven" status flows from the evidence ledger** as the single source of truth; the UI never
  computes proven-ness itself.
- A claim becomes "proven" only via the statistical **referee** (sealed holdout + controls +
  multiple-testing correction); the referee and ledger live in the project (read-only MCP "window" +
  `project-extensions/` gate), not in the shared framework.

## Design Direction

- Visual style: minimal, data-dense, evidence-first — consistent with the existing Trendora UI.
- Mood: skeptical, rigorous, honest. Evidence status is calm and unmissable, never hype.
- Reference: existing Trendora surfaces; badges read like a quiet "proven ✓ / not yet proven" chip.

## Product Shape

### Navigation / information architecture
- Existing nav unchanged: Dashboard | Stocks | Sectors | Themes | Backtest | Research | Data | Watchlist.
- **New: Evidence** (the ledger) added to the persistent nav, reachable in ≤2 clicks.
- Evidence badges appear **inline** on existing score surfaces (Stocks leaderboard, Stock detail,
  Sector/Theme leaderboards, research labs) — each badge links to its ledger entry.

### Canonical values (single source of truth)
- **Evidence status** and **certified-claim** for any (signal, as-of) — computed **once** by the referee,
  stored in the evidence ledger, and displayed identically everywhere a badge appears.
- The three scores (Leadership / Entry Quality / Risk), regime score, market phase, and realized
  forward-returns remain single-source from the existing engine (unchanged).

## Must-have user journeys

- **J-01: Every score shows an evidence status**
  - Steps:
    1. Visit `/stocks`
    2. Observe the leaderboard rows
    3. Assert each row's score area shows an evidence badge reading "Proven" or "Not yet proven"
    4. Assert at least one badge is present and none of the displayed scores lack a status
  - Acceptance: no score on the leaderboard is presented without a visible evidence status.

- **J-02: Drill into the proof behind a score**
  - Steps:
    1. From `/stocks`, click a stock to open `/stocks/{ticker}`
    2. Locate a score with a "Proven" badge and expand/click it
    3. Assert the panel shows: the out-of-sample test result, the control comparison
       (vs SPY/QQQ/sector ETF/random), and the certified-claim id + registration date
  - Acceptance: the user can see *why* a score is considered proven — the test, the controls, and the date.

- **J-03: Unproven / noise signals are honestly marked**
  - Steps:
    1. Find a score or edge whose claim has not been certified (or failed out-of-sample)
    2. Assert the UI shows "Not yet proven" (and, where applicable, "did not beat controls out-of-sample")
       rather than a confident-looking number
  - Acceptance: unvalidated or failed signals are visibly flagged and never presented as confident.

- **J-04: Regime-conditioned evidence**
  - Steps:
    1. Visit the Dashboard and note the current market regime/phase
    2. Open a research lab or the Evidence surface for a regime-conditioned claim
    3. Assert the evidence shown is scoped to and labeled with the regime it applies to
  - Acceptance: evidence is regime-scoped and clearly labeled with the regime it holds in.

- **J-05: Audit the evidence ledger**
  - Steps:
    1. Click "Evidence" in the nav
    2. Assert a list of certified claims renders, each with: hypothesis, out-of-sample verdict,
       control comparison, registration date, and forward-walk score-to-date
    3. Click a claim and assert it links back to the surface(s) whose badge it backs
  - Acceptance: the user can audit every "proven" claim the platform relies on, end to end.

- **J-07: Multi-horizon certified edge surfaced (the loop sees beyond the 20-day horizon)**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for a factor cohort at a
       NON-20 forward-return horizon (1/5/10/60) — e.g.
       `{"kind":"factor","factor":"<key>","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive"}` —
       that the post-decompose gate certifies through the referee BEFORE any code is built
       (a non-PASS verdict blocks the iteration).
    2. Visit `/evidence` and locate the new certified-claim row; assert its horizon is the
       non-20 value and it renders the standard fields (hypothesis incl. horizon, out-of-sample
       verdict, SPY control, registration date, forward-walk score-to-date, "Backs: Research
       factor lab →").
    3. Open `/research/factor-lab` for that factor; assert its cohort at that horizon shows a
       "Proven" badge linking to this ledger entry, while uncertified horizons read "Not yet proven".
  - Acceptance:
    - **Consistency (single source):** the row + factor-lab badge read the canonical
      `GET /api/evidence` payload verbatim; the claim is a NEW entry in the EXISTING
      `certified-claims.jsonl` (no new computing module, no new serving endpoint).
    - **Correctness:** displayed edge / p-value / control byte-match the referee verdict for
      the same as-of — never a UI recompute.
    - **Honest status / anti-goals:** a signal-less factor claim backs ONLY the factor lab,
      never a `/stocks` inline badge (J-01/J-02/J-03 unaffected); "Proven" only with a PASS,
      else "Not yet proven" (anti-goal #1); no return/price/buy-sell language; determinism +
      no-lookahead preserved (scoring ≤ as-of, forward returns > as-of; sealed temporal holdout).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the multi-horizon row +
      badge, viewable via `demo.sh mcp-loop --session-live`.

- **J-08: Multi-factor combination certified edge surfaced on the Combination lab + Evidence**
  - Steps:
    1. The iteration carries a `## Evidence Claim` for a curated 2-factor composite cohort drawn
       from the pre-registered combination candidate set — e.g.
       `{"kind":"combination","cohort":"composite","horizon":20,"direction":"positive","condition":["rs_spy_3m:top:quintile","atr_pct:bottom:tertile"]}` —
       certified by the gate BEFORE any code is built (a non-PASS verdict blocks the iteration).
    2. Visit `/evidence`, locate the new combination certified-claim row, and assert the standard
       fields plus a "Backs: Multi-factor combination lab →" linkback.
    3. Open `/research/factor-combination`, reproduce/select that combination, and assert its
       composite cohort shows a "Proven" badge linking to this ledger entry; uncertified
       combinations read "Not yet proven".
  - Acceptance: same Consistency / Correctness / Honest-status / Walkthrough bar as J-07
    (canonical `GET /api/evidence` single source; byte-match; signal-less ⇒ no `/stocks` badge;
    PASS-gated; no return/price/buy-sell; deterministic; `[NEW]` walkthrough). The combination
    MUST come from the pre-registered candidate set — never an ad-hoc data-mined cohort.

- **J-10: The product surfaces deep (up to ~30-year) price history, honestly bounded per name**
  - Steps:
    1. Price data comes from the committed seed rebuilt from the FREE Stooq provider across the full span
       (~1996→present, as far back as each name's real listing) in the identical
       `date,open,high,low,close,volume` schema with split/dividend back-adjusted `close`; no fabricated
       bars (missing/short history stays short, never synthesized).
    2. Open a long-tenured name (AAPL / MSFT / NVDA); assert the available history / as-of backtest window
       spans well beyond 5 years (back toward ~1996 or the name's real first bar), not the old 2021 floor.
    3. Open a post-IPO name (ARM / COIN / HOOD); assert it honestly shows only its real (short) history.
  - Acceptance:
    - **Consistency:** chart/backtest read the same `daily_prices` the engine scores on; the displayed
      first date matches the committed seed's real first bar for that symbol (no invented dates).
    - **Correctness:** `close` is back-adjusted consistently across the whole span (no discontinuous jump
      at the old 2021 seam); a known split (NVDA/AAPL) is continuous.
    - **Honest status / anti-goals:** no fabricated data; the survivorship disclosure is present wherever a
      multi-year edge/backtest shows; determinism + no-lookahead preserved (scoring ≤ as-of, forward > as-of).
    - **Performance:** pages reading the latest snapshot/ledger (`/stocks`, `/evidence`) stay responsive;
      long-range charts window or downsample the deep history rather than shipping every bar.
    - **Walkthrough:** a `[NEW]` demo-narrator walkthrough of the deeper chart/backtest window.

- **J-11: Every displayed "Proven" edge is re-certified on the new 30-year data — no stale edge survives**
  - Steps:
    1. The historical data basis has been replaced, so EVERY pre-refresh certified-claim (computed on the
       retired ~5-year window) is invalidated. The evidence ledger is regenerated from scratch by the
       referee/gate on the new data — nothing is carried forward.
    2. Visit `/evidence`; assert every row is one the referee re-passed on the 30-year data, and that no
       pre-refresh edge value (old +21.34% / +6.36% / p=0.0004998) is shown unless it independently re-certified.
    3. Cross-check one surviving factor edge on its Research lab: the "Proven" badge + `/evidence` row
       byte-match the regenerated ledger for the same as-of.
  - Acceptance:
    - **Consistency (single source):** badges + rows read canonical `GET /api/evidence`; the regenerated
      `certified-claims.jsonl` is the only source; the two frozen-golden tests (`test_evidence.py`
      canonical golden + `test_staging_ledger_routing.py`) are refreshed to the new values.
    - **Correctness:** every displayed edge/p-value/control byte-matches the regenerated referee verdict —
      never an old carried number, never a UI recompute.
    - **Honest status / anti-goals:** an edge that no longer clears the referee on 30-year data reads "Not
      yet proven" (anti-goal #1); no retired/overfit edge shown as proven (anti-goal #4); determinism
      preserved (seed 20240601); the honest-stop guard is respected.
    - **Walkthrough:** a `[NEW]` walkthrough of the re-certified `/evidence` ledger.

- **J-12: The universe is a broad, point-in-time dynamic set across the deep history — names enter at
  their real IPO and leave cleanly when their data ends; discrete existence never corrupts a number**
  - Steps:
    1. The candidate pool is broadened to the full committed `universe_pool.csv` (~548: current S&P500 ∪
       Nasdaq-100 ∪ prior) with Stooq bars loaded for the pool (not just the ~122 seed names); membership
       at each date is resolved point-in-time by the existing `resolve_members(D)` (history/price/ADV on
       `bars_asof(D)`), no lookahead.
    2. Pick a name that IPO'd mid-history; assert it is ABSENT from the universe/leaderboard on dates
       before it accumulated `min_history_bars` and PRESENT after — no fabricated early rows.
    3. Pick a name whose data ends mid-history; assert it exits membership cleanly at end-of-data, its
       60-day-return/MDD contributions are honest NA/n=0 for horizons running past its last bar, and it
       never produces a misaligned relative-strength score (the `rs_vs` staleness gate excludes stale members).
  - Acceptance:
    - **Consistency:** the leaderboard/methodology membership count reflects `resolve_members(D)` over the
      broadened pool for that date; entries/exits match the membership timeline (J-96).
    - **Correctness:** 60-day return, max-drawdown, and decile ranking are per-`(symbol,date)` with honest
      NA/n=0 for partial existence (no cross-symbol matrix); a stale/ended name never yields a misaligned
      RS score (staleness gate in `resolve_candidate`).
    - **Honest status / anti-goals:** point-in-time entry preserves no-lookahead (admission at D reads only
      bars ≤ D); truly delisted names absent from free Stooq are disclosed, never fabricated; determinism preserved.
    - **Walkthrough:** a `[NEW]` walkthrough of the membership timeline showing entries/exits across the deep history.

- **J-13: The Data Manager page reflects the broadened 548-symbol universe, and its per-date
  availability legend is unambiguous**
  - Steps:
    1. On `/data`, a generic Fetch job operates over the full ~548-symbol pool (not the old ~122), so
       keeping the seed fresh covers every pool name; the "Expand universe" job option is removed (its
       pool-fetch role is now the default Fetch once the 548 pool is the committed default).
    2. In the "Per-date availability" heatmap, assert the legend clearly separates the two DISTINCT
       signals: the cell FILL = price-data completeness (how many stored symbols have a bar that day),
       and the snapshot indicator = whether an immutable scored scan exists for that day. No two encodings
       look alike while meaning different things (no amber-as-"best", no fill-green colliding with a
       snapshot-green).
    3. Hover a date with bars but no snapshot (a backfill gap) and a date with a snapshot; assert the
       tooltip + legend make the difference obvious and explain the Fetch→fills / Backfill→scores workflow.
  - Acceptance:
    - **Consistency:** the Fetch symbol set = the committed 548 pool; the availability numbers still come
      from the same `GET /api/data/availability` (`symbols_with_bars` / `total_symbols`, `snapshot_exists`)
      — a presentation-only clarity change, no data-semantics change.
    - **Correctness:** "full" (fill) and "snapshot" (ring/badge) keep their true orthogonal meanings
      (data-completeness vs scored-scan) — clarified, not merged (they are genuinely different: a day can
      be one without the other).
    - **Honest status / anti-goals:** removing the Expand UI trigger fabricates no data and hides no gap;
      market caps (Expand's other role) either refresh via a retained path or are honestly shown as
      committed/static; no invented dead-name data.
    - **Walkthrough:** a `[NEW]` walkthrough of the clarified availability legend + the 548-symbol Fetch.

- **J-14: The 30-year basis carries deep, honestly-sourced index context (benchmarks + macro), each
  labeled by vendor**
  - Steps:
    1. The seed carries deep index context across the 30-year window: a deep equity benchmark (`^SPX`,
       plus `^NDX`/`^DJI`) from Stooq's world bundle, and `^VIX` re-fetched deep from Yahoo — no fabricated
       bars; a series a source lacks stays honestly short.
    2. On the relevant view (dashboard regime / research), the deep benchmark and the volatility/macro
       overlays render across the deep window (not the old ~5-year floor); the macro proxies
       (`^TNX`/`^DXY`/`^VXN`) stay coherent with the FRED macro series the app shows on `/data`.
    3. Each index/benchmark series discloses its vendor (Stooq / Yahoo / FRED-macro proxy) where surfaced.
  - Acceptance:
    - **Consistency:** charts/regime read the same `daily_prices` the engine scores on; a displayed
      series' first date matches the committed seed's real first bar for that series.
    - **Correctness:** displayed values match the seed; a macro proxy equals its FRED source series (never
      a market index); no recompute; no intra-series vendor-splice seam.
    - **Honest status / anti-goals:** no fabricated bars; the vendor mix is disclosed per series and a
      proxy is never presented as a market index; determinism + no-lookahead preserved.
    - **Walkthrough:** a `[NEW]` walkthrough of the deep benchmark + the vendor-labeled index/macro context.

- **J-15: Core pages and APIs stay fast on the deep basis — measured, budgeted, never regressing**
  - Steps:
    1. With a warm backend in prod mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh` —
       never `dev.sh`, whose `--reload` + per-route `next dev` compile are not product latency),
       measure time-to-interactive of `/stocks`, `/stocks/AAPL` (including the Full-history toggle),
       `/data`, and `/evidence`, and the warm latency of `GET /api/stocks`, `/api/stocks/{ticker}`,
       `/api/data`, and `/api/health`.
    2. Record every measurement in `reports/perf-budgets.md` (the committed budgets table).
    3. Every later iteration that touches the data path re-asserts the committed budgets and records
       the fresh numbers alongside the old ones.
  - Acceptance:
    - **Budgets:** pages interactive ≤ 3 s warm; `GET /api/stocks` ≤ 1.5 s (≤ 0.5 s once item E of the
      fast-platform section lands); `/api/stocks/{ticker}` ≤ 0.3 s (item D); `/api/data` ≤ 1.5 s warm
      and its COLD path completes ≤ 60 s without OOM under the 6144 MB cap (item A); `/api/health`
      ≤ 0.1 s (item G). If a budget is proven infeasible without a correctness trade-off, the budgets
      table may set a different value WITH the measurement attached — the table then IS the contract.
    - **Correctness (byte-identical):** optimized paths return byte-identical values to the canonical
      computation for the same as-of — a projection or cache re-serves stored values, never recomputes.
    - **Honest status / anti-goals:** anything slower than its budget shows an honest progress or
      initializing state, never a frozen or blank frame; determinism + no-lookahead preserved.
    - **Walkthrough:** a `[NEW]` walkthrough showing the measured timings against the committed budgets.

- **J-16: Data jobs (Fetch + Backfill + warmup) are fast and honest about progress**
  - Steps:
    1. Commit the measured baseline to `reports/perf-budgets.md` (current, measured 2026-07-07:
       backfill ≈ 6.2 s/date; per-date snapshot compute 2–8 s; seed load 20.5 s; full warmup pass
       ≈ 124 cadence dates + forward returns).
    2. Land the prescribed optimizations (items A, B, F of the fast-platform section, including F's
       warmup-cache note).
    3. Re-measure the same operations on the same host and commit the new numbers.
  - Acceptance:
    - **Improvement:** per-date backfill wall time improves ≥ 30% vs the committed baseline
      (network-bound fetch transfer time is measured separately and excluded from the target); a full
      warmup pass improves ≥ 30%; the improved numbers become the never-regress budgets.
    - **Correctness (byte-identical):** per-(symbol, date) outputs are byte-identical to the
      unoptimized path — snapshots, forward returns, and membership resolve to the same values.
    - **Honest status / anti-goals:** running jobs keep live progress on `/data` and never report
      done early; no fabricated or partial data marked complete.
    - **Walkthrough:** a `[NEW]` walkthrough of the before/after job timings from the budgets table.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->

- **J-06: vcp_contraction top-decile certified edge surfaced on Evidence + Research factor lab**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for the vcp_contraction top-decile cohort —
       `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":20,"direction":"positive"}` —
       so the post-decompose gate certifies it through the referee (sealed out-of-sample holdout + SPY
       control + multiple-testing deflation) BEFORE any code is built; a non-PASS verdict (FAIL/INSUFFICIENT)
       blocks the iteration.
    2. Visit `/evidence` and locate the new vcp_contraction certified-claim row.
    3. Assert it renders the same fields as the existing claim rows: hypothesis, out-of-sample verdict,
       control comparison (vs SPY), registration date, forward-walk score-to-date, and a
       "Backs: Research factor lab →" linkback.
    4. Open the Research factor lab (`/research/factor-lab`) for the vcp_contraction factor and assert its
       top-decile cohort shows an evidence badge reading "Proven" that links to this ledger entry.
  - Acceptance:
    - **Consistency (single source):** the vcp_contraction ledger row and the factor-lab badge read the canonical
      `GET /api/evidence` payload verbatim (the ledger row re-displays `claims[]`; the badge looks up the
      resolved evidence status — it NEVER recomputes proven-ness or re-fetches from a new path). The vcp_contraction
      certified-claim is a NEW entry in the EXISTING `certified-claims.jsonl` ledger already served by
      `GET /api/evidence` — **no new computing module and no new serving endpoint** are introduced (same
      evidence-status contract value, one additional reader), so the Data Contract's single source of truth
      is preserved (no new shared value to register).
    - **Correctness:** the displayed out-of-sample edge, p-value, and control comparison byte-match the
      referee verdict written to `certified-claims.jsonl` for the same as-of — never a recompute in the UI.
    - **Honest status / anti-goals:** like the Breakout-watch setup claim, the vcp_contraction factor claim carries
      NO per-stock `signal`, so it backs ONLY the Research factor lab and never lights or overwrites a
      `/stocks` inline score badge (J-01/J-02/J-03 unaffected). The factor-lab cohort reads "Proven" ONLY
      because a PASS certified-claim backs it; absent a PASS verdict it must read "Not yet proven"
      (anti-goal #1 upheld). No return promise, price target, or buy/sell signal is shown — only the evidence
      status plus the realized hold-out statistic. Determinism + no-lookahead preserved (scoring ≤ as-of,
      forward returns > as-of; the referee uses a sealed temporal holdout).
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the new vcp_contraction ledger row and the
      factor-lab "Proven" badge is produced (plain-language narration + a real-data screenshot example),
      viewable via `demo.sh mcp-loop --session-live`.

- **J-09: Relative-strength (rs_spy_3m) 60-day-horizon certified edge surfaced on Evidence + Research factor lab**
  - Steps:
    1. The iteration carries a machine-readable `## Evidence Claim` for the rs_spy_3m top-decile cohort at the
       NON-20 60-day horizon — promoted from the pre-registered multi-horizon staging winner
       (`project-extensions/proposer-guidance.md` §4.1 #3; recorded staging block-bootstrap p=0.00049975) via an
       explicit canonical ledger route —
       `{"kind":"factor","factor":"rs_spy_3m","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive","ledger":"canonical"}` —
       so the post-decompose gate certifies it through the referee (sealed out-of-sample holdout + SPY control +
       multiple-testing deflation at the canonical Bonferroni divisor) BEFORE any code is built; a non-PASS verdict
       (FAIL/INSUFFICIENT) blocks the iteration.
    2. Visit `/evidence` and locate the new rs_spy_3m certified-claim row; assert it renders the same fields as the
       existing claim rows: hypothesis (incl. the 60-day horizon), out-of-sample verdict, control comparison (vs SPY),
       registration date, forward-walk score-to-date, and a "Backs: Research factor lab →" linkback.
    3. Open the Research factor lab (`/research/factor-lab`) for the rs_spy_3m factor and assert its top-decile cohort
       at the 60-day horizon shows an evidence badge reading "Proven" that links to this ledger entry, while its
       uncertified horizons (h1/h5/h10/h20) read "Not yet proven".
  - Acceptance:
    - **Consistency (single source):** the rs_spy_3m ledger row and the factor-lab badge read the canonical
      `GET /api/evidence` payload verbatim (the row re-displays `claims[]`; the badge resolves status via the EXISTING
      per-horizon cohort matcher `resolveCohortEvidence` — it NEVER recomputes proven-ness or re-fetches from a new
      path). The claim is a NEW entry in the EXISTING `certified-claims.jsonl` already served by `GET /api/evidence` —
      **no new computing module and no new serving endpoint** (same evidence-status contract value, one additional
      reader position), so the Data Contract's single source of truth is preserved (no new shared value to register).
    - **Correctness:** the displayed out-of-sample edge, p-value, and SPY control byte-match the referee verdict
      written to `certified-claims.jsonl` for the same as-of — never a recompute in the UI.
    - **Honest status / anti-goals:** rs_spy_3m ∉ the three score columns, so the claim carries NO `signal` and backs
      ONLY the Research factor lab — it never lights or overwrites a `/stocks` inline score badge (J-01/J-02/J-03
      unaffected; `proven_signals` stays `{leadership_score}`). The factor-lab cohort reads "Proven" ONLY because a
      PASS certified-claim backs it; absent a PASS verdict it reads "Not yet proven" (anti-goal #1 upheld). No return
      promise, price target, or buy/sell signal is shown — only the evidence status plus the realized hold-out
      statistic. Determinism + no-lookahead preserved (scoring ≤ as-of, forward returns > as-of; the referee uses a
      sealed temporal holdout). The cohort MUST be the pre-registered §4.1 candidate — never an ad-hoc data-mined slice.
    - **Walkthrough:** a `[NEW]`-flagged demo-narrator walkthrough of the new rs_spy_3m ledger row and the factor-lab
      "Proven" badge is produced (plain-language narration + a real-data screenshot example), viewable via
      `demo.sh mcp-loop --session-live`.

<!-- /AUTO:journeys -->

## Anti-goals

- A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
  **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
  values MUST render a "not yet proven" state. *(critical)*
- **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
  claims; never place or simulate orders. *(critical)*
- A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
  for the same as-of date — not merely that the page renders. *(critical)*
- **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
  out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
- **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
  never introduce lookahead anywhere. *(critical)*
- No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
  post-decompose gate. *(critical)*
- No hard-coded credentials, API keys, or tokens in source files. *(critical)*
- **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader
  pools, deeper history) must never crash an existing page or exhaust a service's memory — every
  existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
  boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
  whole-table ORM loads are forbidden on the deep basis. *(critical)*

## Loop mechanics (for the iteration planner)

When an iteration's purpose is to ship a **data-derived** decision-support view — i.e. it presents a
score / ranking / edge as "proven" — the iteration spec MUST include a machine-readable **Evidence
Claim** so the post-decompose gate can certify the edge through the referee BEFORE any code is built.
Iterations that are pure UX / correctness / navigation work (no new "proven" claim) need NO Evidence
Claim and pass the gate automatically.

Write the claim as a fenced JSON block under a `## Evidence Claim` heading, using the same cohort
selectors the Research labs use (mirrors `/api/research/samples`):

```json
{"kind": "factor", "factor": "<factor-key>", "slice_kind": "decile", "decile": 10, "horizon": 20, "direction": "positive"}
```

- `kind`: `factor` | `event-study` | `regime-setup-pattern` | … (a Research-lab cohort)
- selectors: the cohort slice (factor + `decile`/`regime`, or `subject`/`setup`), exactly as in the labs
- `horizon`: forward-return horizon in trading days; `direction`: `positive` | `negative`

The gate runs the referee — a **sealed out-of-sample holdout** + an **SPY control** + **multiple-testing
deflation** (the bar tightens with every claim ever tested) — and appends the verdict to the
certified-claims ledger at `runs/goal-session-<sid>/state/certified-claims.jsonl`. A non-PASS verdict
(`FAIL` or `INSUFFICIENT`) **blocks** the iteration. So propose only an Evidence Claim you have reason to
believe survives out-of-sample, and prefer **narrow, regime-conditioned** cohorts over broad,
data-mined ones — the referee counts independent holdout *dates*, not correlated same-date names, and
will refuse to certify on a sample too thin to believe.

> **Sustaining an open-ended search:** the single global Bonferroni bar above is what the
> "Improvement direction (engineering)" section below replaces for *exploration*. Per-iteration
> Evidence Claims default to a separate **staging** ledger under an online-FDR economy; the
> user-facing `/evidence` ledger (`certified-claims.jsonl`) stays strict Bonferroni and receives
> only deliberately promoted winners (`"ledger":"canonical"`). Build that economy BEFORE widening
> the scan, so the wider aperture has a sustainable economy to run in.

> **Data-basis change (sanctioned ledger reset):** when the historical price seed is rebuilt (the
> ~30-year Stooq extension over the broadened 548 point-in-time universe, in the second "Improvement
> direction" section below), treat ALL prior certified-claims as invalidated — they were measured on the
> retired window and will not reproduce. Regenerate the ledger on the new data BEFORE re-declaring any
> edge "Proven", and refresh the frozen-golden tests. This is the one sanctioned reset of the otherwise
> append-only ledger; J-01..J-09 remain valid contracts (honest badges, correct numbers) but their
> specific certified edges recompute.

## Improvement direction (engineering): open the aperture + sustainable trial economy

The continuous-improvement loop converged because the discovery machinery is structurally narrow,
not because real edges are exhausted. Two coupled upgrades — **build the economy first, then widen
the scan**. (Richer engineering notes were drafted in a planning doc; everything needed is inlined
here.)

**Why it stalled.** (1) The scan enumerates only `factor × horizon-20 × deciles{1,10}` (~22 cells,
SPY control only) in `app/engine/triad_scan.py` `scan_factor_decile_cells`, while the cohort/cert
path already supports horizons 1–60, regime/sector slices, and multi-factor combinations, against a
dense ~1,377-date snapshot. (2) The referee uses one global Bonferroni counter that never resets and
counts failures (`app/engine/referee.py` `certify_edge`; `app/engine/ledger.py` `count_trials`), so
every probe permanently tightens the bar (now `0.05/5 = 0.010`) and a single FAIL is permanent.

**A) Sustainable trial economy (hybrid — build this FIRST).** Add online-FDR (LORD++) as an
*injectable, default-off* deflation policy in the referee, running in a SEPARATE **staging** ledger
where a discovery replenishes testing capacity (so a wide search keeps finding edges). The canonical
`certified-claims.jsonl` served to `/evidence` stays STRICT Bonferroni and receives only deliberately
promoted winners — its "Proven" badge keeps its current family-wise guarantee. FDR is OFF by default
(config); exploration is isolated; the honesty guards (out-of-sample-beats-control gate, block
bootstrap, Thresholdout overfit charge) stay independent of the economy. Seams: new PURE
`app/engine/online_fdr.py` (no RNG/IO, wealth derived from rejection times — zero migration);
`RefereeState.test_level` + `deflation` (default-preserving, so every existing referee test stays
byte-identical); `ledger.rejection_offsets` (derived, no schema change → live ledger `[1,2,4]`);
`verify_edge` threads the economy (stays the ONLY ledger writer); `forward_walk` reproduce-contract
preserved by reconstructing `test_level` from the recorded `required_p`; `EvidenceCfg` typed `FdrCfg`
(defaults reproduce today) + `staging_ledger_path` in `config.yaml`; gate routing in
`project-extensions/gates/verify_claim.py` reads an optional `"ledger"` key per Evidence Claim
(default `"staging"`, explicit `"canonical"` for winners) with `exit 3`-on-non-PASS blocking
unchanged; `run-goal.sh` exports `STAGING_LEDGER_PATH` alongside `LEDGER_PATH`. The 4 existing
canonical entries stay byte-identical (`deflation="bonferroni"`, divisors 1–4 — honest history).

**B) Open the scan aperture (after A). Phase 1:** multi-horizon (config-only:
`config.yaml` triad `horizons: [1,5,10,20,60]`, reuses `compute_factor_lab`) + curated 2-factor
combinations (reuse `compute_factor_combination`; emit the `condition`-string claim form parsed by
`drill_samples`; combination enumerator + selector translation in `triad_scan.py`). Raise
`triad.top_k` (only `ranked[:top_k]` are screened) and the currently-inert `triad.screen.haircut_coef`
so the multiple-testing haircut scales with the wider aperture. A PRE-REGISTERED, config-backed
candidate set — each pair/horizon carrying a one-line economic rationale, mirrored into
`project-extensions/proposer-guidance.md` — is the anti-data-mining keystone: iterate a fixed
hypothesis set, NEVER the full cross-product. Deferred to later phases (NOT this direction):
quantile spreads (D10−D1), regime conditioning (reuse the `regime-phase-factor` kind first), sector
cohorts (event-study sector slice), scoped α-split families.

**Honesty constraint (anti-goal #1 upheld):** FDR controls the false-discovery *rate* and is weaker
than family-wise control — it runs ONLY in staging; the user-facing `/evidence` "Proven" badge stays
Bonferroni-curated. Every verdict records its `deflation` + `required_p` for audit. No unbacked or
overfit edge is ever shown as proven.

## Improvement direction (engineering): 30-year Stooq history over a broad point-in-time dynamic universe

Grow the committed price seed from ~5 to ~30 years using the FREE **Stooq** provider (adapter exists:
`stooq_provider.py`, `make_provider("stooq")`; `config.provider` allows `"stooq"`), broaden the effective
universe to the full ~548-name point-in-time pool, and keep every honesty guarantee. The engine is
shape-agnostic and already discrete-symbol-safe (per-`(symbol,date)` rows, honest NA/n=0, no matrix), and
point-in-time ENTRY already exists (J-93/J-94/J-96) — so the work is data prep, one small membership
hardening, two "use-it" levers, an honest evidence reset, disclosure, and bounding offline cost.
Suggested sequencing: (1) ingest+load 548 × 30y and rebuild DB; (2) membership hardening; (3) evidence
reset + config levers + test refresh; (4) chart perf; (5) Data Manager coherence.

**A) Re-ingest the WHOLE span from Stooq, for the 548-name pool (one consistent adjustment basis).** Route
`scripts/ingest_seed.py` through the provider abstraction (`--provider stooq`) and re-fetch the entire
span (`--start 1996-01-01 --end <today>`, honoring each name's real first bar) for the names in
`data/seed/universe_pool.csv` (~548), NOT just `config.universe.symbols` (~122), and NOT Stooq-deep
spliced onto the existing Yahoo-recent CSVs: the engine trusts `close` to be split/dividend back-adjusted
end-to-end and has ZERO correction logic (`prices.py`/`scoring.py` read close/high/low/volume only), so a
mixed-vendor seam would create an adjustment discontinuity. Ensure `seed_loader.load_prices` loads bars
for the full pool (today it loads only `config.universe.symbols`). Verify Stooq emits the identical
`date,open,high,low,close,volume` schema with adjusted OHLC and confirm its US depth reaches the 1990s for
old names; spot-check a known split (NVDA/AAPL). Names Stooq lacks simply never enter (honest
`below_history`), never padded. Regenerate `data/seed/meta.json`; commit CSVs + meta. **(Status: the
equities span is DONE offline — see §H. Stooq's per-symbol NETWORK endpoint is IP-blocked for this host,
so this span was staged via the existing `--provider stooq-local` path from the local `data/d_us_txt`
bulk archive to `data/seed-stooq-30y/` (583 names, 1996→2026, validated), committed. Do NOT re-fetch it
over the network; the index/macro context is the remaining work in §H.)**

**B) Broaden + harden the dynamic point-in-time universe.** Point-in-time ENTRY already works
(`universe_resolver.resolve_members(D)` screens `read_pool()` = `universe_pool.csv` from `bars_asof(D)`),
so once the 548 have bars, they become eligible and each enters at its real IPO. Add the ONE missing
piece for names whose data ends mid-history: a **recency/staleness gate** in `resolve_candidate`
(`universe_resolver.py`) so a member whose last bar is far from D is excluded (today it gates on bar
count/price/ADV but not recency) — this closes the `rs_vs` positional-misalignment (`indicators.py`) for
stale members. The evidence pipeline (`forward_return`/`max_drawdown`/deciles/referee) needs NO change:
it already returns honest NA/n=0 for partial existence and pools per-`(symbol,date)`. Confirm the
membership timeline (J-96) shows entries/exits across the deep history.

**C) Make the depth actually used.** (1) Rebuild the SQLite DB — `load_prices` is idempotent (no-op if a
symbol has rows), so clear/rebuild `data/trendora.db` (or the `data_manager` `rebuild` job) or the deep
history + new pool names never load. (2) Raise `config.yaml walk_forward.history_years` (currently 2)
toward ~30 — it bounds the quarterly `/api/backtest` window regardless of data extent (cadence stays
`quarterly` → ~120 as-of dates over 30y). (3) Backfill scanner snapshots across the wider window via
`data_manager.run_data_job` (`backfill`/`rebuild`) so the referee's edge-study pool spans the deep
history — but BOUND it (§F): daily cadence for recent years, coarser (weekly/monthly) for the deep history.

**D) Honest evidence reset (load-bearing).** Every row in `certified-claims.jsonl` (7) and
`staging-ledger.jsonl` (7) was computed on the retired window; its edges/p-values (+6.36%, +21.34%,
p=0.0004998, control_n=1137, holdout 279 / in-sample 828, block_length 29/87) will NOT reproduce and MUST
NOT be displayed post-change. Regenerate both ledgers by re-running the gate/referee over the new data
(re-certify only edges that independently re-pass), then refresh the two frozen-golden tests:
`tests/test_evidence.py::test_canonical_ledger_frozen_golden` and `tests/test_staging_ledger_routing.py`.
Also refresh window/count pins in `tests/test_seed_ingest.py` and the offset-date comment in
`tests/test_bar_cache.py` (~"day 150 2021-08"), since the seed start shifts before 2021.

**E) Survivorship — point-in-time over the survivors, honestly disclosed.** The broadened pool + dynamic
entry/exit gives correct point-in-time TIMING for every name Stooq has, but free Stooq has no truly
delisted names, so the residual survivorship (dead names absent) remains — keep + extend
`SURVIVORSHIP_BIAS_LABEL` (`app/engine/forward_testing.py`) to name the 30-year span and "read the edge as
an upper bound," and keep `pool_survivorship()`'s honest `point_in_time_feed_available: False`. Optionally
add representative regime dates to `scanner.bootstrap_dates` (currently `["2022-10-07","2025-04-04"]`) for
2000-03 (dot-com), 2008-11 (GFC), 2020-03 (COVID). A true survivorship-free feed (point-in-time
constituents + delisted prices via a public membership list and/or Sharadar/Norgate) is an out-of-scope
backlog follow-on — NOT this direction; never fabricate dead-name data.

**F) Performance & certification under 30 years × 548 names.**
- *Volume is sub-linear in years* (young universe → sparse deep history): `daily_prices` grows ~2-3×
  even with 548 names; SQLite + the existing `Index(symbol,date)` handles ~1M+ rows trivially.
- *Most pages stay fast:* `/stocks` (latest snapshot, one row/symbol) and `/evidence` (small ledger) don't
  scan raw bars — independent of history depth.
- *One user-visible hotspot — the price chart:* a long-tenured name pulls ~5-7k daily points (vs ~1,356);
  default the chart/backtest to a bounded recent window + opt-in "full history" and/or weekly downsample
  beyond N years (give `/bars` a range/interval param). This is the J-10 "Performance" acceptance.
- *The heavy cost is OFFLINE (build-time), borne once:* the 30y × 548 backfill (more snapshots, more names
  scored per snapshot) can be multi-hour — bound it via the coarser deep-history cadence in §C(3); each
  evidence re-certification runs the bootstrap over a bigger array (seconds → tens of seconds).
- *Certification becomes more DISCRIMINATING:* more observations (deeper history + wider cross-section)
  raise power → a genuine stable edge earns a smaller p-value (easier); the fraction-based sealed holdout
  now spans multiple regimes (dot-com, GFC, COVID, 2021-26) → regime-fragile/data-mined edges correctly
  FAIL the holdout (harder for spurious ones). The Bonferroni bar is UNCHANGED by span (tracks `n_trials`,
  not years). Caveat: residual survivorship can still INFLATE edges (mitigated only by the §E disclosure).
  Net: fewer but more robust certified edges.

**G) Data Manager page coherence with the 548 default.** Three surgical changes:
- *Fetch over 548.* Point the generic-fetch symbol set at the pool: `data_manager._run_job`'s
  `else: symbols = all_seed_symbols(cfg)` branch (~`data_manager.py:2923`, the ~122-based default) →
  `read_pool(seed_dir)` (the 548; `seed_dir` is already threaded, `read_pool` already imported), mirroring
  the existing `is_expand` branch. Backfill already scores the full pool per-date (`resolve_members`) — no
  change. This is the "make the fetch use the new number of symbols" wiring.
- *Remove the "Expand universe" job option.* Delete the `<option value="expand">` (`apps/frontend/app/data/page.tsx`
  ~:2113) and its now-dead supporting code (the `isExpandKind`/`sourceIneligibleForExpand` derived flags,
  the `handleStart` market-cap guard, the `JobForm` props/disabled wiring, the source-eligibility option
  suffix + amber alert, the panel title/copy mentioning expand, the `JobProgressPanel` expand branch, and
  the `ExpandScreenResult` component). The backend still accepts `kind:"expand"` (harmless) and the offline
  `scripts/screen_universe.py` remains the escape hatch. **Decision to make consciously:** Expand is also
  the only on-demand market-cap refresh (J-84 `get_market_caps` → `universe.json`) — since market cap is
  display-only (the per-date resolver drops it), the minimal choice is to accept static committed caps;
  if fresh caps matter, fold `get_market_caps` into the Fetch job or a small dedicated action.
- *Clarify the per-date availability legend (`apps/frontend/components/availability-heatmap.tsx`).* The
  backend emits raw `symbols_with_bars` / `total_symbols` / `snapshot_exists` (`data_manager.compute_availability`);
  the frontend derives "full" = density==1.0 (amber fill `--heat-5`) and "snapshot" = `snapshot_exists`
  (green ring `--pos`). These are ORTHOGONAL (data-completeness set by Fetch vs scored-scan set by Backfill;
  a day can be one without the other — "full but no snapshot" is exactly a backfill gap). Do NOT merge —
  make the distinction unmistakable: split the legend into two labeled groups ("Price data — cell fill"
  vs "Scored snapshot — indicator"), make the density ramp a monotonic single-hue scale so the top bucket
  is not amber (amber is the page's warning color) and does not collide with the 75–<100% green
  (`--heat-4`), give the snapshot indicator an unambiguous non-green treatment, and update the caption +
  tooltip to state each meaning plainly plus the Fetch→fills / Backfill→scores workflow. Color tokens:
  `apps/frontend/app/globals.css` (`--pos`, `--heat-0..5`, `--heat-text-*`) + `tailwind.config.ts`.

**H) Index & macro context for the deep basis (offline sourcing; mixed vendor, honestly disclosed).**
Stooq's per-symbol network endpoint is IP-blocked for this host, so ingest reads Stooq's LOCAL bulk
archives offline via the existing `--provider stooq-local` path (committed): the 548-name equities span
(§A) is already staged from `data/d_us_txt` to `data/seed-stooq-30y/` (583 names). Complete the seed's
index/macro context BEFORE the swap so the swap happens once over one complete seed:
- **Deep equity-index benchmarks `^SPX`/`^NDX`/`^DJI`** — from Stooq's WORLD bundle (`data/d_world_txt`,
  under `data/daily/world/indices/^spx.txt` etc.; single `.txt`, caret kept) via the same `stooq-local`
  path, deep to 1996. Stage as `_SPX/_NDX/_DJI.csv`; usable as a deeper market control (SPY the ETF only
  starts 2005) and for deep index charts.
- **`^VIX`** — a REAL Yahoo OHLCV series (verified: matches the live seed exactly on the 2021–26 overlap)
  → re-fetch DEEP from Yahoo (`--provider yahoo --start 1996`). It is genuinely a Yahoo index.
- **`^TNX`/`^DXY`/`^VXN` are NOT external tickers — do NOT re-fetch them from Yahoo.** They are the app's
  deterministic FRED-macro PROXIES (verified this session: `_DXY` == `macro/dollar_index`, `_TNX` ==
  `macro/credit_spread`×5, `_VXN` a similar flat-OHLC transform; added iter-32/J-92). A Yahoo re-fetch
  (ICE DXY ≈89 vs the app's ≈105; market yield×10 vs the app's `_TNX`) would DESYNC them from the FRED
  macro the app displays elsewhere and silently change their meaning. Keep them coherent with
  `data/seed/macro/`: preserve the existing proxies, or DEEPEN them by extending the FRED macro series
  (FRED carries deep history) and regenerating the proxies deterministically — a macro-subsystem task,
  never a market-index splice.
- **`data/seed/macro/`** (FRED: credit_spread, dollar_index, unemployment_rate, yield_curve) is preserved
  by the swap.
- **Disclosure:** record each index/benchmark series' vendor in `meta.json` (`stooq` / `yahoo` /
  `fred-macro-proxy`) and label it where surfaced; no fabricated bars; a series a source lacks stays
  honestly short; a proxy is NEVER presented as a market index; determinism + no-lookahead preserved.

**Anti-goal guardrails (unchanged):** no fabricated data (missing history / dead names stay absent);
determinism + no-lookahead preserved (seed 20240601; scoring ≤ as-of / forward > as-of; sealed holdout);
every displayed number byte-matches the regenerated referee verdict; no retired/overfit edge shown as
proven; no credentials in source (Stooq needs no API key).

## Improvement direction (engineering): fast platform on the deep basis (measured 2026-07-07)

The 30-year × 587-symbol basis (1.3 GB DB; `daily_prices` 3,270,066 rows; 410 snapshot runs;
`scanner_results` 165,670 rows) made data volume the dominant cost. This section SUPERSEDES §F's
"the heavy cost is OFFLINE" assumption above — measured reality: the online `/api/data` cold path
OOMs (`prices.py:84` whole-table ORM prefill; ~6.8 GB peak vs the 6144 MB `server.memory_cap_mb`
cap), and several endpoints/pages do avoidable full-set work. Every item below preserves the
anti-goals: **byte-identical displayed numbers, determinism/no-lookahead, single canonical
compute/serve per value, honest states.** Items are independent; each lands with its own before/after
measurement recorded in `reports/perf-budgets.md` (J-15/J-16 are the journey contracts).
**Suggested sequencing:** (1) the iter-19 regression pass = sector-null crash fix + item **A**
(unblocks browser-QA); (2) mechanical backend pass = **B + C + D + G + H**; (3) payload & interaction
pass = **E + I**; (4) compute & storage pass = **F + J** (each gated by byte-identical verification).

**A) Bound the bar prefill (the OOM — iter-19, blocking).** `app/engine/prices.py:82-84` `prefill()`
runs `select(DailyPrice).order_by(symbol, date)` + `.all()` → 3.27M hydrated ORM rows at once,
retained in `_by_symbol` for the job. Rewrite as a **streamed, column-projected** load:
`select(DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high, DailyPrice.low,
DailyPrice.close, DailyPrice.volume).order_by(...)` iterated with `.yield_per(batch)` (idiom:
`forward_testing.py:367-378` `_streamed_existing_keys`; ~20 uses in `research.py`), building
lightweight records — a module-level `NamedTuple` or `__slots__` class `Bar` with **exactly those
attribute names** (consumers read `.date/.open/.high/.low/.close/.volume`) — instead of `DailyPrice`
instances. Batch size from config (`research.read_batch_size`, currently 2000, or a new
`data_manager.prefill_batch_size` — no inline literals). Apply the same record type to the lazy
per-symbol path at `prices.py:115`. Expected retained footprint ~0.4–0.5 GB (vs ~3+ GB ORM; the
transient `.all()` spike is eliminated). Preserve `ORDER BY symbol, date` and the `expected_symbols`
semantics so `test_bar_cache.py`'s byte-identical snapshot tests stay green; any new param threaded
through `prefilled_bar_cache → prefill` must be OPTIONAL (monkeypatch shims `test_bar_cache.py:91`,
`:256`; 2-arg call `:102`). ALSO: verify the `compute_coverage` single-flight (`data_manager.py:629-745`)
actually serializes cold-key computes — the OOM log shows ≥6 CONCURRENT prefills from parallel
`/api/data` probes, so either the lock scope excludes `_compute_coverage_uncached`'s prefill or probes
bypass it; enforce one cold compute at a time. Fix the stale `config.yaml` `server.memory_cap_mb`
comment ("~1.3M-row" → the real 3.27M figure).
*Growth leeway (design in now, cheap):* give `prefill` two optional bounds so the cache scales
sub-linearly with future pool growth — `symbols=` (load only pool ∪ benchmarks: the DB already holds
more symbols than the pool serves) and `min_date=` (callers that compute a bounded date range, e.g. a
recent-K-dates backfill, pass `min(target_dates) − max_lookback`; full rebuilds pass None). Both
default to today's behavior. Note in the docstring: `trailing_count` needs full-history **dates**
(cheap scalars), not full-history OHLCV — if the pool ever grows past ~1,500 symbols, split the cache
into dates-only (full depth) + OHLCV (lookback window only) instead of buying more RAM.

**B) Tune SQLite (tiny diff, cross-cutting).** `app/db.py:39-41` sets only `check_same_thread=False`;
the 1.3 GB DB runs journal=delete / synchronous=FULL / 2 MB page cache / no busy_timeout / default
pool 5+10 under a concurrent read+write workload (warmup writes while `/api` reads). In `make_engine`,
add an `event.listen(engine, "connect")` hook applying config-sourced pragmas (new `database.pragmas`
block): `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=30000`, `cache_size=-262144` (256 MB),
`mmap_size=1073741824`, `temp_store=MEMORY`; and size the pool to the workers (`pool_size=10,
max_overflow=20`, config-keyed). WAL+NORMAL is the standard safe pairing for a single-host research
app (worst case: the last commit is lost on power cut — acceptable here; document it). Expected:
writers stop blocking readers during warmup/backfill; commit cost drops ~an order of magnitude;
"database is locked" class errors disappear.
*Growth leeway:* apply the pragma hook **only when the URL is sqlite** and keep it the ONE
dialect-specific site in the codebase — all queries stay ORM-portable, so outgrowing SQLite (see K's
tripwires) is a `database.url` config swap to Postgres, not a rewrite. SQLite with WAL + these indexes
comfortably serves this read pattern to ~10× today's size; the seam matters more than the migration.

**C) Index hygiene (schema + one-off guarded migration at startup).** `models.py:84-87`: the
`UniqueConstraint("symbol","date")` already creates a unique index; the explicit
`Index("ix_daily_prices_symbol_date", ...)` is a **byte-for-byte duplicate (81 MB + a second index
write on every bar insert)** — remove it from the model AND `DROP INDEX IF EXISTS
ix_daily_prices_symbol_date` in a guarded post-`create_db_and_tables` startup step (no alembic in this
repo). Same for `forward_returns`' redundant prefixes `ix_forward_returns_run_id` and
`ix_forward_returns_run_symbol` (both prefixes of the `UNIQUE(run_id,symbol,horizon)` autoindex;
~23 MB). ADD `Index("ix_daily_prices_date", "date")` (`CREATE INDEX IF NOT EXISTS` in the same hook) —
`func.max(DailyPrice.date)` (`prices.py:33`, on ~every request), the availability `group_by(date)`
(`data_manager.py:914-919`) and min/max window scans currently walk 3.27M rows without it. Verify with
`EXPLAIN QUERY PLAN` that `bars_asof` still uses the unique index and `max(date)` uses the new one.
Dropping a redundant index never changes results, only plans.

**D) Stop deserializing the whole leaderboard to serve one row.** `snapshot_serving.py:213-223`
(`stock_detail_payload`) and `watchlist.py:53-58` (`_canonical_rows`) call `stored_stock_rows`, which
`json.loads`es **all ~404 `record_json` blobs** to return 1 (or a few) rows. Add a filtered variant:
query `ScannerResult` `where(run_id==…, ticker==…)` (or `ticker IN (…)` for the watchlist) and
deserialize only those rows. Same serializer, same payload shape — byte-identical responses, existing
API tests stay green. Expected: detail/watchlist latency drops from ~404 `json.loads` to ~1–5.

**E) Lean leaderboard DTO (payload ~2 MB → ~0.2 MB).** `/api/stocks` ships the full detail-row shape
×541 (`apps/frontend/lib/api.ts:276-296`): three `components[]` arrays, `invalidation`, pattern
`detail`+`contractions` — **only the detail page renders those.** Server: in
`snapshot_serving.stocks_payload`, project each row to a summary DTO (ticker, sector, the three scores
as value+bucket+evidence_status WITHOUT `components`, setup status+reason, per-pattern
`flagged`+reason+pivot only, themes, `forward_returns`, and `high_proximity` **lifted to a top-level
field** — it currently hides inside `leadership.components`, forcing a per-cell `.find()`
client-side). Keep the full shape on `/api/stocks/{ticker}` (item D). This is a **projection of the
same canonical stored values** (no recompute — register the summary view in `blueprint.md`'s Data
Contract as a presentation projection of the same canonical rows). Frontend: add `StockSummaryRow` to
`lib/api.ts`, consume it in `app/stocks/page.tsx`; delete the `.find()`-per-cell helpers
(`:904/:931/:938` via `:80/:86`) in favor of the server-provided fields.

**F) Window the scoring inputs (CPU: the 2–8 s/date driver).** `scoring.py:113` and `:339` slice each
member's **entire history ≤ D** (late dates ≈ 5,300 bars) into every indicator, but the longest
lookback is ~252 bars (52-week window; `min_history_bars: 200`; MA/ATR/vol windows smaller). Determine
the TRUE max lookback across `_raw_components` (`scoring.py:119-135`) and the pass-3 detectors (VCP /
pullback / flat-base / hist_volatility / vol_contraction / downside_vol), add config
`indicators.max_lookback_bars` = that max + a safety margin (e.g. 320), and slice `bars[-N:]` before
indicator computation. **Gate: byte-identical verification before adoption** — a one-off harness
compares `score_stocks` output on ≥3 dates × the full pool, windowed vs unwindowed; ANY diff means an
indicator silently depends on deeper history (fix the window; never accept drift). Expected: per-date
snapshot 2–8 s → well under 1 s for late dates (~17× less data per indicator); full rebuild and warmup
scale proportionally. ALSO (same area): `warmup.py:155` runs `backfill_forward_returns` **outside**
the `bar_cache` block that wraps the snapshot loop (`warmup.py:145`) — its per-(run,symbol)
`close_on`/`bars_after` reads (~330k bounded queries per full pass) should run inside the shared cache
context (with item A's lightweight cache this becomes a free in-memory slice).

**G) Make the readiness probe cheap.** `readiness.py:78-80` re-derives the warmup calendar on **every
2 s health poll**: `_warmup_dates` → `walk_forward_asof_dates` materializes all 5,369 SPY ORM rows
(`forward_testing.py:265`), then `get_run_for_date` issues ~124 per-date point queries. Fix:
(1) column-project the SPY calendar (`select(DailyPrice.date).where(symbol == 'SPY')` — date scalars,
not ORM rows) and memoize it keyed on `(latest_date, cfg)`; (2) replace the per-date existence loop
with ONE `select(ScannerRun.asof_date).where(asof_date.in_(cadence_dates))` and a set diff. Budget:
`/api/health` ≤ 0.1 s.

**H) Kill the `/api/data` cold-path N+1.** `data_manager.py:276-281` (`_missing_data_diagnostic`)
runs one `DailyPrice.date` query **per universe member** (~548) on every cold coverage compute.
Replace with one grouped/windowed query (the sibling `_per_symbol_coverage` at `:164-171` already
shows the bulk `group_by` pattern) or read from the active bar cache's `_dates_by_symbol`.

**I) Frontend interaction costs (no data-contract change).**
- *Availability heatmap* (`components/availability-heatmap.tsx:289-328`): ~7,800 `<button>`s (~19k DOM
  nodes) fully re-reconcile on **every hover** because `setHovered` re-runs the whole band map.
  Extract a `React.memo` `HeatCell` (props = precomputed primitives; move
  `parseIsoUTC`/`densityBucket`/range checks into the `bands` memo at `:157`), and hold hover state so
  only the tooltip + the two affected cells re-render (or use one delegated `onMouseOver` on the grid
  container reading `data-*` from the event target). Acceptance: hovering does not re-render the full
  grid (React DevTools profiler count or a dev render-counter).
- *Leaderboard* (`app/stocks/page.tsx`): debounce the search input (~200 ms) before the `visible`
  filter (`:400-418`) and move the URL-reflect `router.replace` (`:306-322`) to the debounced value;
  wrap `StockTableRow` (`:840`) in `React.memo` (row objects keep identity across sorts, so memo
  works); sort a copied array directly with comparators reading item-E's server-provided fields (drop
  the wrap/unwrap double map at `:427-437`).
- *Detail page* (`app/stocks/[ticker]/page.tsx:150,:405`): start the bars fetch in parallel with the
  row fetch (it needs only ticker+asOf+range, not the row) — removes a full round-trip from perceived
  chart load. *Chart* (`components/price-chart.tsx:312`): toggling the regime overlay tears down and
  recreates the entire chart (`chart.remove()` → `createChart` → re-`setData` of ~3.2k points); keep
  the chart instance in a ref and add/remove only the band series on toggle.
- *Cheap wins:* `app/stocks/page.tsx:276-278` re-fetches `/api/methodology` although
  `GlossaryProvider` (`lib/glossary.tsx:41`) already holds it — consume the provider. In `lib/api.ts`
  `getJSON` (`:40-46`), add a small in-memory GET cache for **as-of-pinned URLs only** (responses for
  an explicit `as_of=` are immutable snapshots) so Recent↔Full chart toggles and as-of revisits stop
  re-fetching; latest-view URLs stay `no-store`.

**J) Shrink `record_json` at write (STRUCTURAL — the future-growth driver; after E).**
`scanner_results.record_json` (avg 4,051 B × 165,670 rows = 640 MB, **59% of the DB**) is parsed in
full for every leaderboard read — and its growth slope just changed: **daily snapshot cadence is live
since 2026-06-01** (`scanner.snapshot_cadence.daily_start`), so at current blob size the table grows
≈ 252 runs/yr × ~540 rows × ~4 KB ≈ **+545 MB/year — the DB nearly doubles in ~14 months with zero
new symbols.** Two-part fix: (1) once E lands, persist the summary projection as its own column
(`summary_json`, ~0.3–0.5 KB) at snapshot write; `/api/stocks` reads only `summary_json` (fallback:
derive from `record_json` for pre-migration runs, lazily backfilling); (2) compress `record_json` at
write (zlib ≈ 3–4:1; a `compressed` marker or magic-byte sniff for old rows) with a one-off
maintenance migration over the 165k existing rows. Combined slope: ~+545 → ~+200 MB/yr, and
leaderboard reads stop touching the big blobs entirely. The detail path (item D) still reads the full
blob for its one row. Immutability guardrail: snapshots are evidence — compression/summary re-encode
bytes, never alter values; NEVER thin or prune historical runs (walk-forward + the referee depend on
them).

**K) Measurement, capacity tripwires + ops hygiene.** Add `scripts/measure-perf.sh` (curl-timed warm
endpoint latencies + one bounded K-date backfill timing via the jobs API + a **DB capacity snapshot**:
file size, rows in daily_prices / scanner_results / forward_returns; output appended to
`reports/perf-budgets.md` so the growth **slope** is visible run-over-run) — measurements run against
**prod mode** (`start-backend.sh`/`start-frontend.sh`; `dev.sh`'s `--reload` + `next dev` per-route
compile are not product latency). Surface the same capacity snapshot as a small storage card on
`/data` (the Data Manager already owns this surface — presentation of stored values only, no new
computation). **Capacity tripwires (pre-registered so future planners act instead of rediscovering):**
when ANY of — `daily_prices` > 10M rows, DB file > 5 GB, pool > 1,200 symbols, or a J-15 budget
regresses two measurement runs straight — schedule a capacity iteration: re-baseline, re-check item
A's dates-vs-OHLCV cache split, and evaluate item B's Postgres seam. Growth math for reference: bars
grow ≈ +148k rows/yr (~+4.5%/yr) at today's pool and linearly with pool size; snapshot growth per
item J. The offline pytest fixture cost (~10 h suite) is **test-only and out of scope** for this
workstream. Keep `server.memory_cap_mb: 6144` as the OOM guard; item A must fit comfortably under it
at ≥3× today's row count. New rule going forward: any new loop over "all symbols" or "all dates"
takes its bound/batch/scope from config — never unbounded, never a literal.

**Anti-goal guardrails (unchanged):** no fabricated data; determinism + no-lookahead preserved; every
displayed number byte-matches the canonical engine computation for the same as-of (projections and
caches re-serve stored values, never recompute); honest states everywhere (initializing/progress,
never stale-as-fresh, never a blank crash).
