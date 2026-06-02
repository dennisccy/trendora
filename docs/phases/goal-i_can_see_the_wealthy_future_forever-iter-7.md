# Goal Iteration 7 — Transparent, rule-based, expanded universe (~500 names)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-22
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-13, J-14, J-16, J-17, J-19 (and the full green set J-01…J-21 must stay green)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Universe screen is reproducible & honest.** Universe membership MUST come from the config-recorded screen (no hand-curated list masquerading as a screen); expansion MUST use real committed data only (no fabricated history); breadth and walk-forward labels stay "universe-relative" / survivorship-biased to current membership. *(extends No magic numbers + No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative" (not full-market internals), and walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe).
  - **No lookahead.** *(critical)* Scoring for a snapshot dated D MUST use only bars ≤ D; forward returns only bars > D. Re-fetched bars and any regenerated snapshot/forward-return MUST preserve this.
  - **Snapshots are immutable / On-demand snapshots stay immutable & lookahead-free.** *(critical)* A regenerated snapshot is create-once; never mutate an existing run's result rows; `forward_returns` stays a separate append-only table.
  - **Single source of truth / No recompute in the read path.** *(critical)* The universe is resolved once from the config screen; the six scores + A–E bucket + setup status are computed once and read identically everywhere; the API/frontend MUST NOT recompute a score, bucket, return, or the market-cap/screen value per request.
  - **Risk-Off must gate Actionable.** *(critical)* When the regime is Risk-Off, zero stocks are "Actionable."
  - **No order/execution path. No secrets in source.** *(critical)* Research-only; the offline seed path needs no key; any live-provider key is environment-only.

## GOAL

Replace the hand-curated 158-name stock universe with a **transparent, reproducible, config-recorded screen** that resolves to **~400–500 real US names**, each backed by **committed real daily OHLCV**, with the selection methodology visible in the UI — so every downstream leaderboard, score, and forward-test runs over a credible, rule-defined universe instead of a curated list.

## BACKGROUND

J-01…J-21 are all green; iter-6 opened the new wave (J-20, J-21). The iter-6 evaluator's **primary recommendation** is the foundational data-layer member **J-22**: expand to the rule-based ~500-name universe to grow forward-test sample sizes and unblock the downstream `/research` labs (J-25–J-31), which are sequenced **after** this groundwork (they introduce a NEW `/research` nav home and a re-approval gate — **not** touched this iteration).

Decomposer investigation (evidence, this iter):
- **Data sourcing is feasible.** `apps/backend/scripts/ingest_seed.py` already fetches REAL EOD via the **free, no-key Yahoo chart API** (`query1.finance.yahoo.com/v8/finance/chart`) — not Stooq (whose free CSV is captcha-gated; see lessons iter-3). The same path fetches arbitrary symbols and, via Yahoo's quote endpoint, market-cap/sector at build time. So a real ~500-name expansion is achievable with **zero fabricated data** and **zero committed secrets**.
- **The screen cannot be recomputed by the running app.** The committed seed is **OHLCV-only** (`apps/backend/data/seed/prices/*.csv`); there is **no committed fundamental/market-cap data**. `Stock.market_cap` exists (`models.py:48`) but is `Optional` and unpopulated. Therefore the **market-cap screen MUST be applied at seed-build time** (offline, one-shot) using real fetched fundamentals, and the **result committed** — the request path reads the committed universe and never recomputes membership or market cap (Single source of truth).
- **`config.universe.symbols` is a flat hard list consumed everywhere** (`regime.py:52`, `scoring.py:281,306`, `forward_testing.py:87,506`, `seed_loader.py:49,78`, `api/stocks.py:74`, `api/watchlist.py:118`), and **`stock_sectors` is mandatory per symbol** (validated in `config.py:603`). So expansion = a config + seed operation (add screened symbols + their sector; commit their CSVs), not a calc-code change.
- **Recompute is bounded.** The walk-forward grid is `walk_forward.asof_cadence: quarterly`, `history_years: 2`, plus `scanner.bootstrap_dates: ["2022-10-07","2025-04-04"]` + latest — a modest, fixed set of as-of dates. Widen the **universe width**, NOT the date grid.

**Two risks this spec actively manages (read NOTES):** (1) **regime breadth iterates `cfg.universe.symbols`** (`regime.py:52`), so a wider universe could shift the regime label on the two bootstrap dates that **J-07/J-08 depend on**; (2) a full re-fetch re-bases split/dividend adjustments, perturbing existing **exact** numbers — safe because journeys assert **structural/relational** properties (per `project-template.md`), but the structural invariants must be re-verified.

## IN SCOPE

### Data / seed (one-shot, offline, then frozen + committed)
- [ ] Define a **documented, reproducible candidate pool** as a committed artifact (a transparent **membership rule** — e.g. the union of well-known liquid large/mid-cap index memberships such as S&P 500 ∪ Nasdaq-100, or an equivalent documented listing). The pool list is committed; its origin/rule is documented. This is the "plus any membership rule" half of the screen — NOT a hand-picked code list masquerading as a screen.
- [ ] Extend the **screen+ingest script** (`ingest_seed.py` or a sibling one-shot script) to, for each candidate: fetch real EOD OHLCV **and** real market-cap + GICS sector (Yahoo quote/profile), then **apply the config screen** — `universe.filters.min_price` (from real close), `universe.filters.min_dollar_vol` (from real close×volume ADV), `universe.filters.min_market_cap` (from fetched market cap) — keeping only **passers (~400–500)**. Symbols that fail to fetch or to pass are **logged and omitted** (exactly like the CYBR precedent); **never fabricated**.
- [ ] Fetch the **entire screened universe in a single ingest run** (one window, one adjustment epoch) so all members share a consistent split/dividend-adjustment basis; then **freeze + commit** the CSVs and refresh `apps/backend/data/seed/meta.json` (record source, window, members, per-member screen-pass values, and any omitted/failed symbols honestly).
- [ ] Persist each member's **screen-pass reference values** (market cap, ADV, reference price, sector) as a **committed seed record** (e.g. extend `meta.json` and/or a committed `universe.json`) so the UI can show that each member passed — single source, read-only.

### Backend
- [ ] Update `config.yaml` `universe.symbols` to the resolved **screen passers** (~400–500), and `stock_sectors` to assign **every** member its GICS sector (mandatory; from the build step's fetched sector data). Themes (`themes:`) keep their curated baskets — new names need not all be themed, but any themed member must remain in `universe.symbols` (existing `config.py` validation). Make the `universe.filters` thresholds the **single source** the screen reads (no membership literal in calc code).
- [ ] Populate the `Stock.market_cap` column from the committed screen record at seed-load (`seed_loader.py`) so the stored reference market cap is available read-only; never recompute it in the API/view.
- [ ] Regenerate the bootstrapped snapshots + forward returns over the new universe on the **same** `scanner.bootstrap_dates` + quarterly grid (do **not** widen the date grid). Snapshots stay **create-once, immutable, ≤ D**; forward returns stay append-only, **> D**.
- [ ] **Re-verify (and, only if needed, config-fix) the Risk-Off bootstrap dates:** confirm `2022-10-07` and `2025-04-04` still label **Risk-off** under the expanded universe (regime breadth now spans ~500 names). If a date no longer labels Risk-off, **replace it with a real Risk-off seed date** in `scanner.bootstrap_dates` (config only — no code, no fabrication) so J-07 (zero Actionable in a Risk-off run) and J-08 (≥2 differing dated runs) stay green. Document the check + any swap in the dev handoff.
- [ ] Expose the **universe selection methodology** read-only: extend `GET /api/methodology` with a config-backed **"Universe Selection"** section — the screen thresholds resolved **live** from `universe.filters` via the existing `ref` mechanism (no re-typed numbers), the membership-rule prose, and the resolved **member count** — read from the one canonical resolved universe.

### Frontend
- [ ] On **`/methodology`**, render the new **"Universe Selection"** section: the membership rule, the three screen thresholds (min market cap / min dollar volume / min price, shown from config), and the resolved universe size (~400–500) — same config-backed pattern as the glossary, no hard-coded copy or numbers.
- [ ] On **`/data`** (Data Manager coverage), confirm the **symbol count** now reflects the grown universe (it already serves coverage; it must read the same resolved universe — not a second count). Keep all existing coverage panels working.
- [ ] Keep every honest-limitation label intact: breadth / new-high-low remain **"universe-relative"**; System Health / Backtest walk-forward evidence remains **survivorship-biased** labelled.

### New user-facing capability
The user can read, on `/methodology` (and see the grown count on `/data`), exactly **how the universe is selected** — the membership rule + the liquidity/price/market-cap thresholds from config — and can browse leaderboards/scores/forward-tests over a credible **~500-name** rule-defined universe instead of a 158-name curated list.

### New information displayed
- The **universe selection rule** + the three config screen thresholds (resolved live from config).
- The **resolved universe size** (~400–500), read from the one canonical universe on both `/methodology` and `/data`.
- (Read-only, where surfaced) each member passed the screen — backed by the committed per-member screen-pass values.

### New user actions
None — J-22 is descriptive/read-only. No new buttons or forms (universe expansion is a config + seed operation performed at build time, not a runtime user action; the existing `/data` fetch/backfill controls are unchanged).

### UI surface changes
- `/methodology`: one new **"Universe Selection"** section (config-backed).
- `/data`: symbol-count reflects the grown universe (no structural change to the page).
- All existing leaderboards/detail/health/backtest pages now render over the wider universe (more rows, larger forward-test `n`).

### Product surface delta
Trendora's rankings and forward-tested evidence become materially more credible: the universe is a transparent, reproducible screen over real data (~500 names) rather than a curated 158, and the selection logic is openly documented in-product — directly serving the "earn trust / no hand-picked list" mandate.

### Blueprint conformance
No new nav home and **no nav-skeleton change**. J-22 surfaces on the **existing** `/methodology` and `/data` homes (per `blueprint.md` IA notes for the new wave). **No `blueprint.reapproval-requested` is written this iteration.** The `/research` labs (J-25–J-31) — the only pending nav-skeleton addition — are explicitly out of scope.

### Data-contract additions
One new canonical value, registered additively in `blueprint.md`:
- **Universe membership + selection screen** — resolved **once** from the config-recorded screen by the offline seed-build/screen step (the result is the committed `universe.symbols` + per-member `Stock.market_cap`/sector + committed screen record); the **screen rule + thresholds + resolved size** are served read-only by `GET /api/methodology` (thresholds resolved live from `universe.filters`), and the **member count + coverage** by `GET /api/data`. **Both read the same resolved universe — neither recomputes membership or market cap.** Not a second computation of any existing score/return/bucket.

## OUT OF SCOPE

- **J-23 / J-24** (multi-timeframe bars + chart timeframe selector) — next data-layer step; not this iter.
- **J-25–J-31** (the `/research` Factor Lab + Setup & Pattern Lab, volatility family, synthesis) — require the new `/research` nav home + a blueprint re-approval; deferred.
- **J-28** (additional detected patterns) — deferred.
- **Widening the walk-forward date grid** (`asof_cadence`, `history_years`, `bootstrap_dates` count) — keep the date set fixed; only the universe **width** grows. (Swapping a single bootstrap date to a real Risk-off date is allowed *only* if the expansion changes that date's regime label.)
- **Changing any scoring weight / threshold / bucket edge / decision rule** — tuning is not part of J-22.
- **Live Data Manager runtime fetch semantics (J-17)** beyond it naturally reporting the grown coverage — do not alter the live-fetch/backfill job behavior.
- Any **fundamental data beyond the single market-cap reference value** needed for the screen (no P/E, earnings, etc.).

## DEFINITION OF DONE

- [ ] `config.universe.symbols` resolves to **~400–500 real names**, each defined by the **config-recorded screen** (membership rule + `universe.filters` thresholds) — not a hand-curated list; every member has committed real OHLCV and a `stock_sectors` sector.
- [ ] Seed-build/screen step is **reproducible** (documented, re-runnable) and used **real data only**; failed/omitted symbols are logged honestly; **no fabricated bars/scores**; **no committed secret**.
- [ ] `/methodology` shows the **Universe Selection** section (membership rule + the three thresholds from config + resolved size); `/data` shows the grown symbol count; both read the **one** resolved universe.
- [ ] Breadth/new-high-low stay **"universe-relative"**; walk-forward evidence stays **survivorship-biased** labelled.
- [ ] **J-22 passes via browser-qa-agent.**
- [ ] **Required-still-passing journeys remain green** — especially **J-07** (a Risk-off bootstrap run still shows **zero Actionable**), **J-08** (≥2 differing dated runs), **J-01** (regime label valid + counts/breadth render), **J-02** (ranked rows + sector/Actionable filters narrow), **J-03/J-04** (≥3 ranked themes/sectors), **J-05/J-06** (detail scores == leaderboard, ≥3 components), **J-09/J-10** (by-bucket/control-group render with `n`), **J-11** (watchlist add validates against the new universe + survives restart), **J-13/J-14** (as-of replay + per-date scorecard), **J-16** (VCP filter/badge/detail/glossary/by-VCP), **J-17** (coverage reflects growth), **J-19** (attribution slices consistent with aggregate). All J-01…J-21 stay green.
- [ ] No anti-goal violation introduced (re-verify the critical seams: no-lookahead, immutable snapshots, single-source/no-recompute, Risk-Off gating, no fabricated data, no order path, no secrets).
- [ ] Unit/integration tests pass (existing suite green over the new universe + the new screen/universe tests below); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-7-dev.md`, explicitly documenting: the candidate pool + its rule, the screen application, the re-fetch/freeze decision, the Risk-off bootstrap-date re-verification (+ any swap), final member count, and any omitted symbols.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-22:** on `/methodology` read the Universe Selection rule + the three config thresholds; confirm the resolved universe size is ~400–500 (and `/data` shows the same grown count); confirm `/stocks` renders many more ranked rows than before; confirm the screen/thresholds shown match config.
  - Regression sweep (full flows, distinct evidence per the iter-6 lesson — **serialize Chrome access; assert live DOM/URL before each capture; de-dup by sha256**): **J-07** (open a Risk-off run → zero Actionable), **J-02** (sector + Actionable filters narrow rows), **J-01** (dashboard regime + counts + breadth render), **J-06** (a named stock's three scores identical leaderboard↔detail), **J-16** (VCP filter → badge → detail → glossary → System Health by-VCP), **J-09** (by-bucket + control groups render with `n`), **J-11** (add a screened name + persistence), **J-17** (coverage symbol count grew).
- **Unit/integration (assert exact values + an edge/failure case):**
  - **Screen application:** every resolved member **passes** all three config thresholds (price / dollar-volume / market-cap) against its committed reference values; a fixture candidate **below** a threshold is **excluded** (failure path) — assert exclusion, not just inclusion.
  - **No magic numbers:** the screen reads thresholds only from `config.universe.filters`; existing `test_no_magic_numbers` (and the config-validation suite) stays green over the expanded `universe.symbols` + `stock_sectors` (every universe symbol has a sector; every theme member is in the universe).
  - **No-lookahead** unchanged and re-asserted over the new universe (as-of-D snapshot uses only bars ≤ D; forward returns only bars > D) — the existing walk-forward no-lookahead test must pass over the expanded seed.
  - **Single source of truth:** a stock's three scores + bucket read identically via `GET /api/stocks` (list) and `GET /api/stocks/{ticker}` (detail) for a sampled new name; the served `market_cap`/screen value comes from storage (not recomputed).
  - **Risk-Off gating:** the chosen Risk-off bootstrap run yields **zero** Actionable under the new universe (a code-level assertion in addition to the browser check).
  - **Coverage/universe consistency:** `GET /api/data` symbol count == `len(resolved universe)` == the count surfaced on `/api/methodology` (one source, no drift).
- **Error cases:**
  - A candidate that fails to fetch (or returns an empty/partial series) is **omitted and logged**, never interpolated/fabricated (assert the build step omits it).
  - A candidate below any screen threshold is **excluded** from membership.
  - Provider failure in the (unchanged) live path still surfaces an explicit error with **no fabricated prices** (J-17 contract preserved).

## NOTES

- **Apply the lessons (episodic memory):**
  - *iter-3 (data provider):* Stooq free CSV is captcha-gated; the working real-data path is the **no-key Yahoo chart API** already in `ingest_seed.py`. Use it. Do **not** introduce a keyed provider or commit any key.
  - *iter-6 (concurrent Chrome corruption + duplicate shots):* if both the `qa` agent and `browser-qa-agent` drive Chrome (port 9222), **serialize** — one vacates before the other captures; assert live state (`data-testid`/URL/values) immediately before each screenshot; **de-dup evidence by sha256** (the `TC-15` byte-identical bug recurred in iter-3 and iter-6 — do not let a "before/after" claim rest on a duplicated image).
  - *iter-2 (re-verify rigor):* a single-screenshot surface check does NOT satisfy a multi-step acceptance — exercise J-22's full read flow and the regression flows end-to-end.
  - *iter-2/3/6 (process):* full-depth iters in this session have repeatedly finished **without `status.json` / `auditor` handoff** while QA claims one exists — do not block on or trust that artifact; verify the critical seams in source.
- **Reproducibility decision (state it in the handoff):** re-fetch the **entire** screened universe in one shot for a single adjustment epoch, then freeze+commit. Existing names' exact numbers may shift slightly from re-based split/dividend adjustment; this is acceptable because every must-have journey asserts **structural/relational** properties (ranking order, same-value-in-two-places, zero-Actionable-in-risk-off, a number renders, filters change rows), not exact score values (`project-template.md`). The dev MUST re-verify these invariants, not assume them.
- **Highest-risk seam — J-07/J-08:** the regime label on `scanner.bootstrap_dates` is universe-dependent (`regime.py:52`). After expansion, **verify** `2022-10-07` and `2025-04-04` still label Risk-off; if not, pick a **real** Risk-off seed date from the expanded data and swap it in config (no code, no fabrication). This is the single most likely regression — handle it deliberately.
- **Recommended:** given the candidate-sourcing + screen-application design fork and the broad blast radius, run the **product-manager** (architecture planning) step before implementation to lock the candidate pool, the screen-application mechanism, the committed-record shape, and the re-fetch/freeze plan. This is a heavy, foundational data iteration — plan before coding.
- **Honesty over hitting a number:** ~400–500 is the target band; if real screened passers land slightly outside it, prefer the **honest** screened result (and document it) over padding with names that don't pass the screen. Never fabricate to hit the count.
- This iteration deliberately does **not** start the `/research` labs; it is the data foundation that makes their evidence (and J-23/J-24's factors) credible. The labs come next, with their nav re-approval.
