# Goal Iteration 2 — Indicators + Market Regime + Sector Leaderboard (first canonical values)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04, J-01
  - **J-04 (Sector / industry Leaderboard)** — FULL target; expected to flip to **passing** via browser-qa.
  - **J-01 (Daily dashboard at a glance)** — **PARTIAL** this iteration. Only the **Market Regime panel, market breadth %, data-as-of timestamp, and Top Sectors list** become real. The **candidate counts** (# Actionable / Breakout-watch / Pullback-watch) and **Top Themes** depend on per-stock scoring + theme scoring, which land in **iter-3**. **Do NOT expect J-01 to flip green this iteration** — it remains `failing` (partially advanced) until iter-3 completes "rest J-01".
- **Required-still-passing journeys:** none (no journey is currently `passing`; all 11 are `failing` per `journey-history.json`).
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical — this iteration is the FIRST live test of it)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical — the `bars_asof` accessor + its boundary test are the groundwork this iteration lays)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative" (not full-market internals).
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.

## GOAL

Compute the first real **canonical values** — a **Market Regime** (0–100 score + one of six labels) and ranked **Sector / industry leadership scores** — once in a backend engine and serve them so the **Sector Leaderboard (`/sectors`)** ranks every sector/industry ETF (RS-vs-SPY, distance-from-52-week-high, trend label) and the **Dashboard (`/`)** shows the regime, market breadth, data-as-of date, and the top sectors — all read-only, deterministic against the frozen seed, with no client-side recomputation.

## BACKGROUND

iter-1 built the deterministic spine (config loader, 8-table schema, `SeedProvider`, a committed real-EOD seed of 158 symbols spanning 2021-01-04→2026-05-28, `/api/health`, and the dark Next.js shell with styled empty states). The iter-1 coherence audit is **COHERENCE-PASS** (no consolidation debt). The evaluator returned **CONTINUE** and recommended iter-2 at **full** depth: the indicator engine, the Market Regime engine, and sector/industry leadership scoring, lighting up **J-04** plus the regime/top-sector portions of **J-01**.

This iteration introduces the **first canonical values**, so the *Single source of truth* anti-goal is now live and is the central risk: each value must be computed in exactly one module and served from exactly one endpoint, with the Dashboard's "Top Sectors" reading the **same** `/api/sectors` data the Sector Leaderboard reads. The *No lookahead* discipline is established now via an as-of accessor (`bars_asof(d)` → bars with date ≤ d) that all engine math flows through — the full walk-forward proof arrives in iter-6, but the boundary and its unit test land here.

**Lessons applied (from `lessons.md`):**
- *Browser-driven steps disagreed in iter-1 because the managed `next dev` server flapped.* Unlike iter-1 (empty states), the iter-2 pages **require live backend data** — if the backend or frontend is down, the pages render the explicit "unavailable" state, not the journey. Browser-QA MUST confirm **both** servers are up and stable before judging, and verify by inspecting the evidence directory (screenshots on disk), not a single verdict.
- *Read the frozen seed only.* This iteration MUST NOT re-fetch live data; all math reads the committed seed via the DB (`daily_prices`). Re-fetching would make later walk-forward evidence irreproducible.

## IN SCOPE

### Module-naming reconciliation (do this first — resolves the iter-1 carry-forward)
The approved `blueprint.md` Data Contract is the enforced coherence contract and already names the computing modules `app.engine.*`. Create the package **`apps/backend/app/engine/`** and place every canonical computing module under it, matching the blueprint verbatim. The design doc's flat `app/<module>/` names are superseded by `app/engine/<module>` for the enforced contract. After this iteration the coherence-auditor's canonical-source map must resolve unambiguously to `apps/backend/app/engine/...`.

### Config (additive — single source of tunables; NO literal lands in code)
- [ ] Add an **`indicators:`** section: MA periods `[20, 50, 150, 200]`, RS lookback windows for 1m/3m/6m (trading days), ATR period, 52-week-high window, volume-average period, and a `min_history_bars` floor below which long MAs are reported NA (never fabricated). *(values illustrative — tune later; the point is they live in config)*
- [ ] Add a **`sectors:`** section: the sector-score component **weights** (e.g. `rs_spy_1m`, `rs_spy_3m`, `rs_spy_6m`, `ma_stack`, `dist_from_high`, `vol_trend`) and the **trend-label cutoffs** (score → trend label).
- [ ] Extend the existing **`regime:`** section with **score→label cutoffs** (`label_edges`) mapping a 0–100 score to exactly one of the six existing `regime.labels`. Keep the existing `weights` + `vix_threshold`. *(The label strings already exist; only the cutoffs are missing today.)*
- [ ] `app/config.py` must **validate** these new sections (typed; explicit `ConfigError` on missing/invalid — e.g. label_edges that don't cover 0–100, or weights that don't sum sanely) — never a silent default.

### Backend — `apps/backend/app/engine/`
- [ ] **`prices.py` — as-of accessor** `bars_asof(session, symbol, d)` → the symbol's `daily_prices` rows **with date ≤ d**, ascending. This is the no-lookahead boundary; **all** engine math reads bars through it and never touches a bar with date > d.
- [ ] **`indicators.py` — pure functions** on a price series (no DB): `sma`, `rs_vs(series, benchmark)`, `atr_pct`, `dist_from_high` (distance below the rolling/52-week high, %), `ma_stack` (is price above the configured MAs / are they stacked bullishly), `vol_trend`. Pure, deterministic, unit-tested. Periods come from `config.indicators`.
- [ ] **`buckets.py` — the single bucketing function** `to_bucket(score)` → A/B/C/D/E using `config.buckets` edges. This is the ONLY place A–E is derived (the Data Contract already registers `app.engine.buckets:to_bucket`). Used to label the Sector Score this iteration.
- [ ] **`regime.py` — Market Regime engine** `score_regime(session, asof)` → `{score: 0–100, label: <one of the six>, breadth_above_50dma: %, breadth_above_200dma: %, new_high_low: …, components: [{name, contribution, …}], asof_date}`. Inputs (weights from `config.regime`): index MA-stack (SPY/QQQ), **market-wide universe breadth** above the 50- and 200-DMA, universe-relative new-high/new-low, and the VIX gate (`^VIX` vs `config.regime.vix_threshold`). Label derived from `score` via `config.regime.label_edges`. Breadth/new-high-low are **universe-relative** and must be labelled as such where displayed.
- [ ] **`sectors.py` — Sector/industry leadership** `score_sectors(session, asof)` → a list ranked by **Sector Score** (descending), one row per **sector ETF (the 11 GICS SPDRs) and per industry-group ETF**, each row: `{ticker, kind: "sector"|"industry", name, score: 0–100, bucket: A–E (via `to_bucket`), rs_vs_spy: <numeric>, dist_from_52w_high_pct: <numeric %>, trend_label, components: [{name, contribution, …}], rank}`. Weights/cutoffs from `config.sectors`. **SPY is the RS benchmark and is excluded from the ranked rows** (it is `kind="index"`, not a sector; a sector's RS-vs-SPY is measured against it). Short-history ETFs (e.g. WGMI, BKCH, GEV) MUST be handled gracefully — long MAs/RS report NA rather than crashing or fabricating.

### Backend — `apps/backend/app/api/`
- [ ] **`GET /api/sectors`** (`app/api/sectors.py`) → serves `score_sectors(asof=latest_data_date)`. **Canonical and only** endpoint for Sector Score (per the Data Contract). Registered under `/api` in `main.py` like `health`.
- [ ] **`GET /api/dashboard`** (`app/api/dashboard.py`) → serves the regime panel: `{regime: {score, label, components}, breadth: {above_50dma_pct, above_200dma_pct, label: "universe-relative"}, asof_date, candidate_counts: null, top_themes: null}`. **Canonical and only** endpoint for the Market Regime value (per the Data Contract). `candidate_counts` and `top_themes` are returned **explicitly null/pending** (computed in iter-3) — never a fabricated number. Registered under `/api`.
- [ ] The as-of date for both endpoints defaults to the **latest available data date** = `max(daily_prices.date)` (deterministic; the frozen seed makes it reproducible).

### Frontend (`apps/frontend/`)
- [ ] **`lib/api.ts`** — add typed `fetchSectors()` and `fetchDashboard()` clients (re-format only; **no** score/bucket/return computed client-side). Add matching TypeScript interfaces.
- [ ] **`/sectors` page** — replace the empty state with a **dense ranked table** (reuse `Card`/`Badge`, tabular-nums, palette tokens): columns ticker · kind (sector/industry) · **Sector Score (A–E bucket foregrounded + raw 0–100)**, colour-graded green→red · **RS-vs-SPY** (numeric) · **distance-from-52w-high %** · **trend label**. Each row exposes its **component breakdown** (expandable/tooltip) — explainability, no bare numbers. SPY not present as a ranked leader (excluded as benchmark). Loading, empty, and explicit **"Backend unavailable"** states (no fabricated rows).
- [ ] **`/` (Dashboard) page** — replace the empty state with: a **Market Regime panel** (the six-label badge + numeric 0–100 score + its component breakdown), a **market-breadth figure** labelled **"universe-relative"**, a **"Data as-of <date>"** indicator, and a **Top Sectors** list (top ≥3) that **fetches `/api/sectors`** and slices the top N — the SAME data the Sector Leaderboard shows. **Candidate counts** and **Top Themes** render an explicit **"pending — arriving in a later iteration"** placeholder (not zeros, not fabricated). Loading + "Backend unavailable" states included.

### New user-facing capability
A user can open `/sectors` and see every sector and industry ETF ranked by a real Sector Score with its RS-vs-SPY, how far it sits below its 52-week high, and a trend label — and expand any row to see which components drove the score. On `/` they can read today's market regime (label + score + why), the universe-relative breadth, the data date, and the strongest sectors at a glance.

### New information displayed
Market Regime score + label + components; market breadth (% of universe above 50-/200-DMA, universe-relative); data-as-of date; per-sector/industry Sector Score (A–E + raw), RS-vs-SPY, distance-from-52w-high %, trend label, and component breakdown.

### New user actions
Expand a sector row to reveal its component breakdown. (No forms/mutations this iteration; the pages are read-only views.)

### UI surface changes
`/sectors` becomes a populated ranked leaderboard table; `/` becomes a populated dashboard (regime panel + breadth + data-as-of + top sectors, with pending placeholders for counts/themes). No new routes — both pages already exist in the IA.

### Product surface delta
The product shows its first real analytical output: the market-regime read and the sector/industry leadership ranking that the rest of the funnel (stocks → setups) will sit beneath. It begins to "rank and explain" rather than show empty shells.

### Blueprint conformance
No new pages and no nav change — `/sectors` (Sectors) and `/` (Dashboard) are existing Information-Architecture homes in `blueprint.md`. All displayed values are **already registered** in the Data Contract (Market Regime row; Sector score row incl. RS-vs-SPY / dist-52w / trend label; breadth on the dashboard row; A–E bucket row). A small **additive clarifying note** is added to the Data Contract recording (a) the `app.engine.*` modules live under `apps/backend/app/engine/`, (b) iter-2 computes these values **on-request, deterministically** from the frozen seed and persistence to the snapshot tables lands in iter-5, and (c) the Dashboard's Top Sectors read the canonical `/api/sectors`. This is additive only — **no nav-skeleton change, no re-approval requested.**

### Data-contract additions
**None new.** Every value displayed this iteration is already in the Data Contract. The only edit to `blueprint.md` is the additive clarifying note described above. No value introduced this iteration may be computed or fetched by a second code path — the Dashboard reads regime from `/api/dashboard` and sectors from `/api/sectors`, and the frontend recomputes nothing.

## OUT OF SCOPE

- **Per-stock scoring** (Leadership / Entry Quality / Risk), **bucketing of stock scores**, **theme scoring**, the **Stock & Theme Leaderboards**, **candidate counts**, and **Top Themes** on the dashboard → **iter-3** (J-02, J-03, J-06, rest of J-01). The dashboard shows these as explicit "pending" placeholders.
- **Setup classification** and regime-gating of Actionable → iter-4/iter-5.
- **Stock Detail** page (chart + breakdowns) → iter-4 (J-05).
- **Scanner snapshots / immutable `scanner_runs` history / persistence of scores / Scanner Runs pages** → iter-5 (J-07, J-08). iter-2 computes on-request only; it MUST NOT create snapshot/score tables or pre-empt the immutability machinery.
- **Walk-forward, forward returns, System Health** → iter-6 (J-09, J-10).
- **Watchlist** → iter-7 (J-11).
- **Populating the `industries` reference table + an industry→sector taxonomy**, and **internal sector breadth** (needs a stock→sector mapping that is not populated this iteration). J-04 is satisfied by ranking the sector + industry **ETFs** with RS-vs-SPY / dist-52w / trend label; the taxonomy and internal breadth are deferred.
- **Any live/network data fetch.** Read the committed seed only.

## DEFINITION OF DONE

- [ ] **J-04 passes via browser-qa:** `/sectors` renders sector/industry ETFs **ranked by Sector Score**; the top row shows a numeric **RS-vs-SPY**, a **distance-from-52w-high %**, and a **trend label**; **SPY is not ranked as a leader against itself** (excluded as the benchmark).
- [ ] **J-01 partial verified (NOT expected to flip green):** `/` shows the regime **label (one of the six) + numeric 0–100 score**, a **universe-relative breadth %**, a **data-as-of date**, and a **Top Sectors** list (≥3, each with a score) sourced from `/api/sectors`; candidate counts and Top Themes show an honest **pending** placeholder (no fabricated numbers).
- [ ] **Single source of truth holds:** regime computed only in `app.engine.regime` and served only by `/api/dashboard`; sector scores computed only in `app.engine.sectors` and served only by `/api/sectors`; A–E derived only in `app.engine.buckets`; the Dashboard's Top Sectors read `/api/sectors` (no second computation); the frontend recomputes nothing. (Coherence-auditor must return COHERENCE-PASS.)
- [ ] **No lookahead groundwork:** all engine math reads bars via `bars_asof` (date ≤ d); a unit test proves `bars_asof` excludes bars with date > d and includes date = d.
- [ ] **No magic numbers:** every period / weight / cutoff / bucket edge used in regime, sector, indicator, and bucket math comes from `config.yaml`; a grep finds no such literal in calculation code.
- [ ] **Explainable:** every displayed regime and sector score carries its named component breakdown (present in the API and surfaced in the UI).
- [ ] **Honest limitations:** breadth and new-high/new-low are labelled "universe-relative" wherever shown.
- [ ] **No fabricated data:** backend-unreachable → pages show explicit "unavailable", never fabricated scores/rows; short-history symbols report NA, not invented values.
- [ ] **No anti-goal violation introduced** (no order/execution path; no secrets; no snapshot mutation — none created).
- [ ] **Unit tests pass; no regressions** (the existing 25 backend tests still pass; `npm run build` still compiles + typechecks).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (Chrome MCP):**
  - **J-04 (full):** load `/sectors` with the backend up; assert multiple rows ranked by Sector Score (non-increasing), the top row shows a numeric RS-vs-SPY + dist-from-52w-high % + trend label, and SPY is not a ranked leader. Capture screenshots to the evidence directory.
  - **J-01 (partial):** load `/`; assert the regime label is one of the six with a numeric score, a universe-relative breadth % renders, a data-as-of date renders, and ≥3 top sectors render with scores; assert candidate counts / Top Themes show the pending placeholder (not fabricated numbers). Capture screenshots.
  - Confirm **both** the managed backend and frontend are running and stable before judging; verify via the on-disk evidence directory (lesson from iter-1).
- **Unit/integration (pytest, exact asserted values — not "something returned"):**
  - `app.engine.indicators`: `sma`, `rs_vs`, `atr_pct`, `dist_from_high`, `ma_stack`, `vol_trend` on small hand-computed fixtures with exact expected values.
  - `app.engine.prices.bars_asof`: includes date = d, excludes date > d (no-lookahead boundary).
  - `app.engine.regime.score_regime`: score ∈ [0,100]; label ∈ the six configured labels; label mapping correct **at the `label_edges` boundaries**; breadth ∈ [0,100]; components present.
  - `app.engine.sectors.score_sectors`: list ranked descending by score; each row carries RS-vs-SPY + dist-from-52w-high + trend label + components; **SPY excluded** from ranked rows.
  - `app.engine.buckets.to_bucket`: correct letter at each config edge (A/B/C/D boundaries and E below D).
  - **Determinism:** the same `asof` date yields identical regime + sector outputs across repeated calls (frozen seed).
  - `GET /api/sectors` and `GET /api/dashboard` via `TestClient`: response shape + that served values equal the engine outputs (no recompute drift); `/api/dashboard` returns null/pending candidate_counts + top_themes.
- **Error cases:**
  - A symbol with fewer than `config.indicators.min_history_bars` bars → long MAs/RS report NA; no crash; no fabricated value.
  - Missing/invalid new config (e.g. `regime.label_edges` absent or not covering 0–100, `sectors.weights` missing) → explicit `ConfigError`, never a silent default.
  - Backend unreachable from the frontend → explicit "Backend unavailable" state (no fabricated scores).

## NOTES

- **Why full depth:** broad backend math (indicators + regime + sectors), the **first canonical values** (engaging the critical *Single source of truth* anti-goal), the no-lookahead `bars_asof` boundary, and real unit tests beyond a browser smoke — exactly the criteria for the full 11-step pipeline. The prior evaluator also recommended full.
- **Coherence is the central risk this iteration.** Keep exactly one computing module and one serving endpoint per value, and make the Dashboard reuse `/api/sectors` for Top Sectors. A second computation or a second endpoint for a registered value is exactly what the coherence-auditor hard-fails.
- **Sequencing note for the evaluator:** iter-2 computes regime + sectors **on-request** (deterministic, frozen seed). Persistence into immutable `scanner_runs` / `sector_scores` tables, the "scan ran at" timestamp, and the Scanner Runs history are **deliberately deferred to iter-5** per the roadmap — not an omission. The displayed "Data as-of <date>" is the honest as-of data date and becomes the run timestamp once runs persist.
- **J-01 framing:** please score iter-2 on J-04 flipping to passing and J-01 *partially advancing*; a still-`failing` J-01 is expected and correct here (full pass at iter-3), not a regression.
- `industries` table population, internal sector breadth, and the industry→sector taxonomy are deferred (see OUT OF SCOPE) — they are not required for J-04 and would add taxonomy-design scope.
