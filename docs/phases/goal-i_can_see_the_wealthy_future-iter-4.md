# Goal Iteration 4 — Stock Detail: price+MA chart, volume, theme chips, computed invalidation (J-05)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative" (not full-market internals), and walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - The frontend MUST NOT store auth tokens in `localStorage` (applies only if auth is ever added; this version has no auth).

## GOAL

Complete the Stock Detail page (`/stocks/[ticker]`) so a user opening a leader (e.g. `NVDA`) sees a price + moving-average candle chart with a volume series, theme-membership chips, and a concrete, server-computed invalidation level — alongside the three explainable scores that already render — turning **J-05** green.

## BACKGROUND

iter-3 built the canonical three-score record and the `/api/stocks/{ticker}` detail endpoint; the detail page already renders the setup status, reason, and the three scores with component breakdowns (this is what proved **J-06**). The page itself states the remaining pieces are deferred to "the next iteration" (`apps/frontend/app/stocks/[ticker]/page.tsx:139-143`). J-05 is exactly those remaining pieces: a price+MA chart, a volume series, theme-membership chips, and a **concrete invalidation level** ("below 50-DMA at $X"). The eval for iter-3 recommends iter-4 at **full** depth for J-05, and the roadmap (`project-template.md`) agrees (iter-4 = Setups/reasons/invalidation + Stock Detail chart → J-05).

This is **full** depth: it crosses both tiers, adds a new frontend charting dependency (none installed today), adds a new backend bars/MA-series endpoint, adds a new `config.decision_rules.invalidation` block, and needs new unit tests beyond a browser smoke. `classify_setup` today returns only `{status, reason}` — **the invalidation level does not exist yet** and must be computed canonically.

The iteration's headline single-source risk: the **50-DMA appears in three places** — the chart overlay, the invalidation level, and the scoring `extension`/`support_nearby` components. All three MUST come from the one canonical `app.engine.indicators:sma` over the config MA period, so they can never disagree. See NOTES for the standing lessons that bear directly on this iteration (browser-qa frontend-up reconciliation; reuse the canonical MA, don't recompute; confirm the new dependency is no-key; emit the audit handoff).

## IN SCOPE

### Backend
- [ ] Add a rolling moving-average **series** helper to `apps/backend/app/engine/indicators.py` — e.g. `sma_series(values, period)` returning a list aligned to the input (NA/`None` for each index with fewer than `period` prior values, then the simple moving average). It MUST reuse the same windowing definition as the existing `sma` so that `sma_series(values, p)[-1] == sma(values, p)` for every `p` (single source for the MA definition; no second MA formula). Period stays an argument (no literal).
- [ ] Add a new canonical endpoint `GET /api/stocks/{ticker}/bars` (add to the existing `app/api/stocks.py` router) that returns, for the as-of date (`latest_data_date`, same as the other stock routes):
  - `asof_date`, `ticker`
  - `bars`: ascending OHLCV rows (`date, open, high, low, close, volume`) read **only** via `bars_asof(session, ticker, asof)` (date ≤ as-of — no lookahead)
  - `ma`: a map keyed by each period in `config.indicators.ma_periods` (e.g. `"20"`, `"50"`, `"150"`, `"200"`) → the rolling `sma_series` aligned 1:1 with `bars` (each element a number or `null`/NA where history is too short)
  - Return `503` when no price data exists and `404` for an unknown ticker — never a fabricated/empty-but-OK row (mirror the existing `/api/stocks/{ticker}` contract).
- [ ] Add a new `config.yaml` block `decision_rules.invalidation` naming the invalidation MA basis — e.g. `invalidation: { ma_period: 50 }` (the period MUST be one of `indicators.ma_periods`). No invalidation literal may live in calculation code.
- [ ] Compute the **invalidation level** once in `app.engine.scoring:score_stocks` (where the bars + canonical `sma` are already available) and attach it to each per-stock row as a structured field, e.g. `row["invalidation"] = { "basis": "50-DMA", "ma_period": 50, "level": <sma value or None>, "price": <latest close or None>, "note": "Invalid below the 50-DMA at $<level>" }`. The `level` MUST be the canonical `sma(closes, config invalidation ma_period)` — the SAME value whose rolling series ends the `/bars` chart. The **human note string is built in the backend** (single source); when the MA is NA, emit an honest note (e.g. "Invalidation level NA — insufficient history") and `level: null`, never a fabricated number.
- [ ] Compute **theme membership** once in `score_stocks` from the canonical `config.themes` map and attach it to each per-stock row as `row["themes"] = [{ "slug": ..., "name": ... }, ...]` (every theme whose member list contains the ticker; empty list if none). This reuses the SAME `config.themes` definitions that `score_themes` ranks — no second mapping.
- [ ] Because invalidation + themes ride on the shared `score_stocks` row, both `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) carry them identically — do NOT add them only on the detail path (that would create a second shape and risk J-06).

### Frontend
- [ ] Install a charting library. **Lightweight-Charts** (TradingView, MIT, client-side only, no key/account) is the intended choice per the stack doc for candles+MAs+volume; Recharts is the documented fallback for simple panels. The install MUST pass the supply-chain security gate; confirm the dependency pulls no key/credential and no network-callout at runtime.
- [ ] On `apps/frontend/app/stocks/[ticker]/page.tsx`, replace the placeholder paragraph (lines ~139-143) with:
  - A **price candle chart** (OHLC) with the moving-average overlays drawn **from the server `ma` series** returned by `/api/stocks/{ticker}/bars` — the frontend MUST NOT compute any MA from the close array (re-format/plot only).
  - A **volume series** (histogram/sub-pane) from the same `bars`.
  - **Theme-membership chips** from `row.themes` (label or link to the existing `/themes` home; no new route).
  - The **invalidation note** rendered verbatim from `row.invalidation.note` (do not assemble the "$X" string client-side), with an honest treatment when `level` is null.
- [ ] Add a typed fetcher `fetchStockBars(ticker, signal)` + response interface to `apps/frontend/lib/api.ts`, and extend `StockRow` with `themes` and `invalidation` (keep "RE-FORMATS server values only — NO business computation here").
- [ ] Loading / empty / error states for the chart consistent with the existing dark workstation styling (skeleton while loading; the existing "Backend unavailable" / "Unknown ticker" states must still work). Numbers stay monospace/tabular.

### New user-facing capability
A user can open any leaderboard row's Stock Detail and study the chart (candles + 20/50/150/200-DMA overlays + volume), see which themes the stock belongs to, and read a concrete, explainable invalidation level that tells them where the idea is wrong — all without the page ever recomputing a value.

### New information displayed
Price candle chart with MA overlays; volume series; theme-membership chips; a concrete invalidation level/note (e.g. "Invalid below the 50-DMA at $X").

### New user actions
Open Stock Detail from a leaderboard row (existing); click a theme chip to reach `/themes` (optional link). No new mutating actions.

### UI surface changes
`/stocks/[ticker]` only — the chart panel, volume sub-pane, theme chips, and invalidation note are added below/alongside the existing setup+reason header and the three score cards. No other page changes.

### Product surface delta
Stock Detail graduates from a scores-only consistency proof into the full per-stock research view the goal describes — chart + explainable scores + theme context + invalidation — while preserving the single-source guarantee that the detail scores are byte-identical to the leaderboard.

### Blueprint conformance
All work lives under the existing **Stocks** IA home: `/stocks/[ticker]` (row-reached Stock Detail), already in `blueprint.md`. Theme chips link to the existing **Themes** (`/themes`) home. **No nav-skeleton change → no `blueprint.reapproval-requested`.**

### Data-contract additions (already registered in `blueprint.md` this iteration)
- **Price / MA / volume series (per ticker, as-of)** — computed by `app.engine.prices:bars_asof` (bars) + canonical `app.engine.indicators:sma`/`sma_series` (MA overlays over `config.indicators.ma_periods`); served by `GET /api/stocks/{ticker}/bars`. MAs computed server-side; frontend plots the server series and never recomputes a MA.
- **Invalidation level (per stock)** — computed once in `app.engine.scoring:score_stocks` from the config-named invalidation MA (`decision_rules.invalidation.ma_period`, default 50) via canonical `sma`; rides on the existing `/api/stocks` + `/api/stocks/{ticker}` rows. (Refines the existing "component breakdown + reason + invalidation" contract row from "emitted by the scoring fns" to this concrete source.)
- **Theme membership (per stock)** — derived in `score_stocks` from the canonical `config.themes` map; rides on the existing stock rows.

No EXISTING contract value is given a second computation or a second serving path. The three per-stock scores keep their single source (`score_stocks` → `/api/stocks` (+`/{ticker}`)).

## OUT OF SCOPE

- Scanner snapshots / persistence (`models.py` stays unchanged) and the Scanner Runs pages — **iter-5** (J-07, J-08).
- Per-snapshot score history on the detail page ("scores across past snapshots") — that is a nice-to-have (Key Capability #15) and depends on snapshot persistence (iter-5); J-05 acceptance does NOT require it. Exclude.
- Walk-forward / System Health / Watchlist — iters 6–7.
- Any new earnings-gap data (the `gap_climax` Risk component stays NA, as in iter-3).
- Re-tuning any scoring weight or changing existing score math (J-01–J-04/J-06 must not move).
- Intraday data, options, additional indicators beyond what the chart needs.

## DEFINITION OF DONE

- [ ] **J-05** passes via browser-qa-agent: from `/stocks`, clicking a leader (e.g. NVDA) opens `/stocks/NVDA`; a price+MA candle chart and a volume series render; each of the three scores shows its A–E bucket, 0–100 value, and ≥3 named components (already true — must not regress); theme-membership chips, setup status, reason, and a concrete invalidation level all render.
- [ ] **Required-still-passing** J-01, J-02, J-03, J-04, J-06 remain green — in particular J-06: NVDA's three scores/buckets are still byte-identical on `/stocks` and `/stocks/NVDA` after adding the new row fields, and the leaderboard still renders all rows.
- [ ] No anti-goal violation introduced (see checks below).
- [ ] Unit tests pass (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`); frontend builds (`cd apps/frontend && npm run build`); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-4-dev.md`.
- [ ] **Audit handoff is emitted** at full depth (it was missing iter-2 and iter-3 — see NOTES).

## TESTING REQUIREMENTS

- **Browser (J-05):** Navigate `/stocks` → click a leader row → land on `/stocks/<ticker>`. Verify (with a screenshot as evidence, saved to the iteration evidence dir): the **chart canvas actually renders** (candles visible, MA overlay lines visible, a volume series visible — not just that the page loaded); theme chips render; the invalidation note renders with a concrete level; the three score cards still show bucket+number+components. Capture the unknown-ticker and backend-down states still behaving honestly.
- **Unit/integration (backend):**
  - `test_indicators.py`: `sma_series` correctness — NA for the warm-up prefix, correct rolling values after, and the invariant `sma_series(values, p)[-1] == sma(values, p)`.
  - `test_api_engine.py` (or a new `test_bars` module): `GET /api/stocks/{ticker}/bars` returns ascending bars all with `date ≤ asof` (no-lookahead), `ma` keyed by every `config.indicators.ma_periods` entry and aligned to `bars` length; `404` for an unknown ticker; `503` when no data.
  - Scoring/setup tests: the per-stock row now carries `invalidation` and `themes`; `invalidation.level == sma(closes_asof(ticker), config invalidation ma_period)` (the chart/scoring/invalidation 50-DMA agree); a short-history ticker yields `invalidation.level is None` with an honest note (no fabrication); `themes` matches the reverse of `config.themes`.
  - **J-06 guard:** assert `/api/stocks/{ticker}` row (including the new `invalidation` + `themes`) equals the matching row in `/api/stocks` (extend the existing list==detail guard).
  - `test_no_magic_numbers.py`: the new `decision_rules.invalidation.ma_period` is sourced from config; no invalidation/MA literal added to calc files (extend `CALC_FILES` coverage to the new series helper / endpoint as needed).
- **Error cases:** unknown ticker → 404 (chart endpoint too); no price data → 503; MA not computable (short history) → NA/`null` in both the `ma` series (gap) and `invalidation.level` (honest note), never fabricated.

## NOTES

Lessons from `lessons.md` that apply directly to this iteration (surface them to dev/reviewer/QA/evaluator):

1. **Browser-qa SKIP-vs-PASS flap has recurred three times (iters 1–3)** — the dedicated browser-qa step keeps probing a dead `next dev` and SKIPS while QA mode-2 starts its own server and captures the real evidence. J-05 is **canvas-rendered** (Lightweight-Charts draws to `<canvas>`), so a "page loaded" check is not enough and stale/missing screenshots are likely if the server flaps. **Structural ask for the orchestrator:** ensure the dedicated browser-qa owns/self-heals its frontend (start it if down, as QA mode-2 does) or share one managed server; the evaluator must reconcile J-05 from the on-disk evidence PNGs, not a lone SKIP/PASS verdict, and must confirm the chart canvas is actually populated.
2. **Reuse the canonical MA — do not introduce a second MA computation.** The chart's MA overlays, the invalidation level, and the scoring `extension`/`support_nearby` components must all derive from the one `app.engine.indicators:sma` over the config period. The frontend must plot the server `ma` series and never compute a moving average from the close array. (Same class of "two-sources-for-one-number" the coherence-auditor failed on in spirit at iter-2.)
3. **Confirm the new dependency is free/no-key before relying on it** (iter-1 lesson). Lightweight-Charts is MIT, client-side, no account/key — verify the install adds no credential and no runtime network callout; it must clear the supply-chain gate. If Lightweight-Charts is problematic, the documented fallback is Recharts (still no key) — document any pivot in the handoff, preserving the No-secrets anti-goal.
4. **Emit the audit handoff** — it was not produced at full depth in iter-2 and iter-3. This is a full-depth iteration; the audit handoff must be written.

Anti-goal checks specific to this iteration:
- *No lookahead (critical):* the `/bars` endpoint reads only `bars_asof` (date ≤ as-of); the chart shows no bar after the as-of date.
- *Single source of truth (critical):* one MA definition feeds chart+invalidation+scoring; invalidation note built server-side; list==detail row stays byte-identical (J-06). Frontend re-formats/plots only.
- *No magic numbers:* invalidation MA basis from `config.decision_rules.invalidation`; chart MA periods from `config.indicators.ma_periods`.
- *No fabricated data:* short-history MA = NA (chart gap + invalidation `null` + honest note); 404/503 preserved.
- *Snapshots immutable (critical):* `models.py` unchanged — no persistence this iteration (deferred to iter-5).
- *No order/execution path (critical) & No secrets:* no broker/order path; the charting lib is no-key — re-grep the new/changed source to confirm.

Reference: iter-3 eval (`runs/goal-session-i_can_see_the_wealthy_future/iter-3/eval.md`) and the iter-3 coherence PASS; blueprint Data Contract rows for invalidation / theme membership / price-MA-volume series were registered this iteration (additive, no nav change).
