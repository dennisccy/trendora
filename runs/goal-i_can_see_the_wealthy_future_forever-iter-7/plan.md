# goal-i_can_see_the_wealthy_future_forever-iter-7 Execution Plan

**Target journey:** **J-22** — replace the hand-curated universe with a **transparent, reproducible,
config-recorded screen** resolving to **~400–500 real US names**, each backed by committed real daily
OHLCV + GICS sector + a stored screen-pass market cap; the selection methodology surfaced on
`/methodology` and the grown count on `/data`.
**Depth:** full (one-shot offline seed-build/screen + backend config/load + 2 read endpoints + 2 frontend
sections; broad blast radius — every leaderboard/score/forward-test now runs over ~4× the universe).
**Critical anti-goals in play:** *Universe screen reproducible & honest* (no hand-curated list masquerading
as a screen; real data only), *No fabricated data* (failed/below-threshold candidates omitted+logged),
*No magic numbers* (screen reads only `universe.filters`), *No-lookahead* + *Snapshots immutable* (regen
stays create-once, ≤ D / append-only > D), *Single source of truth / No recompute* (one resolved universe,
read identically), *Risk-Off gates Actionable* (J-07 — the highest-risk regression), *No secrets in source*.

> **This is a heavy, foundational DATA iteration. The spec explicitly recommends a product-manager
> architecture pass before coding. The architectural decisions are pre-locked below as documented
> assumptions; the developer SHOULD still verify the two hard prerequisites (network reachability +
> a real no-key market-cap/sector source) BEFORE the costly full re-seed.** See *Risks & prerequisites*.

## Verified against source before planning (real names this plan builds to)
- **Current universe is 122, not 158.** `config.yaml` `universe.symbols` = **122** stock tickers
  (`config.yaml:46`). `meta.json.symbols_ok = 158` counts universe **+ ETFs + ^VIX** (index 4 + sector 11
  + industry 20 + ^VIX = 36 → 122+36=158). The **ranked-stock** universe (`/stocks` rows, `regime` breadth,
  forward-test `n`) is **122**. So J-22 grows `universe.symbols` 122 → ~400–500; assert "≫ before", not "not 158".
- **Screen thresholds already exist in config** (`config.yaml:42-45`): `universe.filters.min_market_cap:
  2_000_000_000`, `min_dollar_vol: 50_000_000`, `min_price: 10`. These ARE the single source the screen reads.
- **`ingest_seed.py` fetches OHLCV only** via the no-key Yahoo chart API (`query1.finance.yahoo.com/v8/finance/chart`,
  `ingest_seed.py:43`); builds its symbol list from `config.universe.symbols` + ETFs (`:114-121`); writes
  `meta.json` (`:148-159`). It does **NOT** fetch market cap or GICS sector today, and does **NOT** apply a
  screen. → J-22 must EXTEND it (or a sibling one-shot script) to fetch market cap + sector and apply the screen.
- **`seed_loader.py` leaves `Stock.market_cap` NULL** (`models.py:48` exists, unpopulated). `load_reference_data`
  iterates `config.universe.symbols` and reads `config.stock_sectors[ticker]` for the sector (`seed_loader.py:78,81`).
  → J-22 populates `market_cap` from the committed screen record here.
- **`regime.py:52` iterates `cfg.universe.symbols`** for breadth (% above 50/200-DMA, net new-high/low).
  → **HIGHEST-RISK SEAM**: a ~500-name universe shifts the breadth-derived regime score, which can flip the
  label on the two `scanner.bootstrap_dates` that **J-07/J-08** depend on.
- **`scanner.bootstrap_dates: ["2022-10-07","2025-04-04"]`; `walk_forward` history_years 2 / quarterly /
  horizons [1,5,10,20,60] / min_sample 30.** → keep the date grid FIXED; only universe **width** grows.
- **`methodology.py::build_catalog(config)`** resolves each threshold via `ref` → live config value
  (`config.py` `resolve_ref`); served verbatim by `GET /api/methodology`; all refs validated at boot
  (`config.py:626`). `methodology.py` is in the **no-magic-numbers** forbidden-literal set — introduce no int
  literal there (`len(config.universe.symbols)` is a read, not a literal).
- **`data_manager.compute_coverage` counts DISTINCT `DailyPrice.symbol`** (`data_manager.py:82`) — that
  count includes ETFs+^VIX, so it is **not** the same number as `len(universe.symbols)`. → must reconcile
  (see Coherence guardrails) so the "universe size" shown on `/data` == the one on `/methodology`.
- **Validation already enforces the invariants** (`config.py:599-611,582-596`): every `universe.symbols`
  entry MUST have a `stock_sectors` mapping to a valid `etfs.sector` name; every theme member MUST be in
  the universe. Count-based tests scale automatically (`test_db.py`, `test_scanner.py` use
  `len(config.universe.symbols)`); `test_config.py` asserts `>= 100` (stays true).

## What to Build

### A. Data / seed — one-shot, offline, then frozen + committed (the core of J-22)
- **Commit a documented candidate pool** as a reproducible artifact (e.g.
  `apps/backend/data/seed/universe_pool.csv` or `.json`): the **union of well-known liquid large/mid-cap
  index memberships** — **assume S&P 500 ∪ Nasdaq-100** (≈500–510 unique names) — with its **origin + as-of
  date documented** (in the file header and the dev handoff). This committed list is the "membership rule"
  half of the screen — it is the POOL, not the final universe, and it is NOT a hand-picked code list (it is
  a transparent index membership). The screen is applied to it.
- **Extend the screen+ingest step** (`ingest_seed.py` or a sibling one-shot `screen_universe.py`) to, for
  **each** candidate: fetch real EOD OHLCV (existing Yahoo chart path) **and** real **market cap + GICS
  sector** (Yahoo quote/quoteSummary — confirm a working no-key route first; see Risks), then **apply the
  config screen** from `universe.filters`: keep only names with reference `close ≥ min_price`, ADV
  (`close × volume`) `≥ min_dollar_vol`, and `market_cap ≥ min_market_cap`. **Passers ≈ 400–500** become the
  universe. **Symbols that fail to fetch, return empty/partial series, or fail any threshold are logged and
  OMITTED — never fabricated** (the CYBR precedent).
- **Single-shot re-fetch of the ENTIRE screened universe** (one window, one split/dividend-adjustment epoch)
  so all members share a consistent adjustment basis; then **freeze + commit** the CSVs and refresh
  `meta.json` (source, window, members, per-member screen-pass values, and any omitted/failed symbols, honestly).
- **Persist each member's screen-pass reference values** (market cap, ADV, reference price, sector) as a
  **committed seed record** — a new `apps/backend/data/seed/universe.json` (preferred; clean single source)
  and/or extended `meta.json` — so the stored market cap and "this member passed the screen" facts are
  read-only single-source.

### B. Backend
- **`config.yaml`** — set `universe.symbols` to the **resolved screen passers** (~400–500) and add a
  `stock_sectors` entry (valid `etfs.sector` GICS name) for **every** member (mandatory; from the build
  step's fetched sector). Keep `universe.filters` as the single screen source. Themes keep their curated
  baskets (new names need not be themed; any themed member must be in `universe.symbols` — existing validation).
- **`seed_loader.py`** — populate `Stock.market_cap` from the committed screen record at load (read-only;
  never recomputed in the API/view). Sector loading path is unchanged (already config-driven).
- **Regenerate bootstrapped snapshots + forward returns** over the new universe on the **SAME**
  `scanner.bootstrap_dates` + quarterly grid (do **NOT** widen the grid). Snapshots stay **create-once,
  immutable, ≤ D**; forward returns stay append-only, **> D**.
- **Re-verify the Risk-Off bootstrap dates (CRITICAL, J-07/J-08):** confirm `2022-10-07` **and**
  `2025-04-04` still label **Risk-off** under the expanded universe. If a date no longer labels Risk-off,
  **swap it for a real Risk-off seed date** (config-only — `scanner.bootstrap_dates`; no code, no
  fabrication) and document the swap. This is the single most likely regression.
- **Expose the universe methodology read-only** — extend `GET /api/methodology` with a config-backed
  **"Universe Selection"** payload: the three screen thresholds resolved **live** via the existing `ref`
  mechanism (no re-typed numbers), the **membership-rule prose** (from config), and the **resolved member
  count** = `len(resolved universe)` read from the one canonical universe. Render it as a distinct section,
  not as a setup/pattern entry (must not break the catalog-completeness assertion or the setup-filter vocab).
  Add the membership-rule prose + a `universe.selection`/`methodology.universe` config block as needed
  (config-sourced; no hard-coded copy).
- **Reconcile the `/data` universe count** — surface a **universe-member count** on `GET /api/data` equal to
  `len(resolved universe)` (the same value `/api/methodology` shows), so the two pages agree and the
  consistency test passes. Keep the existing total-coverage (DailyPrice distinct) figure as coverage detail.

### C. Frontend
- **`/methodology`** — render the new **"Universe Selection"** section: the membership rule, the three
  thresholds (shown from config), and the resolved universe size (~400–500) — same config-backed pattern as
  the glossary; **no hard-coded copy or numbers**.
- **`/data`** — show the grown **universe size** reading the same resolved universe (not a second count);
  keep every existing coverage panel + the fetch/backfill controls working.
- **Keep all honest-limitation labels intact** — breadth / new-high-low stay **"universe-relative"**;
  System Health / Backtest walk-forward evidence stays **survivorship-biased** labelled.

## Agents Required
- developer: yes — one developer covers all tracks.
  - backend-data: yes — the screen+ingest one-shot (fetch OHLCV + market cap + sector, apply screen, freeze
    + commit seed + `universe.json`); `config.yaml` universe/stock_sectors update; `seed_loader` market-cap
    population; snapshot+forward-return regeneration; bootstrap-date re-verify/swap; `/api/methodology`
    Universe-Selection section; `/api/data` universe-count reconciliation; the new unit/integration tests.
  - frontend-ux: yes — `/methodology` Universe-Selection section; `/data` grown universe size; preserve
    honest-limitation labels. Small, additive UI (J-22 is read-only — no new buttons/forms).

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/scripts/ingest_seed.py` (extend) **or** `apps/backend/scripts/screen_universe.py` (new) —
  candidate-pool screen + market-cap/sector fetch + screen application + freeze/commit + meta/universe record.
- `apps/backend/data/seed/universe_pool.(csv|json)` (new) — committed candidate pool + documented origin/as-of.
- `apps/backend/data/seed/universe.json` (new) — committed per-member screen-pass record (cap/ADV/price/sector).
- `apps/backend/data/seed/prices/*.csv` (regenerated + ~280–380 new) — one real OHLCV CSV per resolved member.
- `apps/backend/data/seed/meta.json` (refresh) — source/window/members/omitted, honestly.
- `config.yaml` — `universe.symbols` → screen passers; `stock_sectors` for every member; membership-rule
  prose + any `methodology.universe`/`universe.selection` config; bootstrap_dates swap **only if** required.
- `apps/backend/app/seed_loader.py` — populate `Stock.market_cap` from the committed record.
- `apps/backend/app/engine/methodology.py` + `apps/backend/app/api/methodology.py` — Universe-Selection
  section (thresholds via `ref`, prose from config, resolved size from the one universe; no int literal).
- `apps/backend/app/api/data.py` (+ `app/engine/data_manager.py` if needed) — universe-member count == `len(resolved universe)`.
- `apps/backend/tests/` — new: screen application (pass + below-threshold exclusion), universe/coverage
  consistency, market-cap single-source, Risk-Off gating on the chosen bootstrap date; existing
  no-magic-numbers / no-lookahead / config-validation suites must stay green over the expanded universe.
- `apps/frontend/lib/api.ts` — types for the Universe-Selection payload + the `/data` universe count.
- `apps/frontend/app/methodology/page.tsx` — render the Universe-Selection section.
- `apps/frontend/app/data/page.tsx` — show the grown universe size (single resolved value).
- `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` — flip the J-22 row from
  "target iter-7" to "built iter-7". **No nav-skeleton change; no `blueprint.reapproval-requested`** this iter.

## UI Evolution
- **New user-facing capability:** the user can read on `/methodology` (and see the grown count on `/data`)
  exactly **how the universe is selected** — the membership rule + the liquidity/price/market-cap thresholds
  from config — and browse every leaderboard/score/forward-test over a credible **~400–500-name** rule-defined
  universe instead of 122 curated names.
- **New information displayed:** the universe selection **rule** + the **three config thresholds** (live from
  config); the **resolved universe size** (read from the one canonical universe on both `/methodology` and `/data`).
- **New user actions:** none — J-22 is descriptive/read-only (expansion is a build-time config+seed operation;
  the existing `/data` fetch/backfill controls are unchanged).
- **UI surface changes:** `/methodology` gains one **"Universe Selection"** section; `/data` symbol/universe
  count reflects the grown universe (no structural page change); all existing leaderboards/detail/health/
  backtest pages now render over the wider universe (more rows, larger forward-test `n`).
- **Navigation changes:** none (both surfaces are existing homes; no sidebar/nav-skeleton change).

## Visual Requirements
- **Component patterns:** reuse existing — the methodology page's config-backed section/card pattern (mirror
  the glossary `EntryCard`) for the Universe-Selection section; the `/data` coverage `Card`/metric pattern for
  the universe-size figure. No new component-library pieces.
- **Layout:** dense dark analytical workstation, unchanged; the Universe-Selection section slots into the
  existing `/methodology` stack; the universe size slots into the existing `/data` coverage panel.
- **Key visual effects:** palette tokens only; numbers monospace/tabular (`tabular-nums`); thresholds shown
  as `$2B` / `$50M` / `$10`-style formatted reads of the config values — no ad-hoc hex, no re-typed numbers.
- **States to handle:** loading/empty/error already exist on both pages (keep); if the methodology payload
  lacks the universe section, show the existing empty/error treatment — never a hard-coded fallback number.

## Key Test Scenarios
- **(unit) Screen application (pass + FAILURE path):** every resolved member **passes all three** config
  thresholds against its committed reference values; a fixture candidate **below** a threshold (price OR
  dollar-vol OR market cap) is **EXCLUDED** — assert exclusion, not just inclusion; a candidate that fails to
  fetch / returns empty is **omitted + logged**, never interpolated.
- **(unit) No magic numbers:** the screen reads thresholds only from `config.universe.filters`; existing
  `test_no_magic_numbers` + config-validation stay green over the expanded `universe.symbols` + `stock_sectors`
  (every universe symbol has a valid sector; every theme member is in the universe).
- **(unit) No-lookahead re-asserted over the new universe:** as-of-D snapshot uses only bars ≤ D; forward
  returns only bars > D — the existing walk-forward no-lookahead test passes over the expanded seed.
- **(unit) Single source of truth:** a sampled new name's three scores + bucket read **identically** via
  `GET /api/stocks` (list) and `GET /api/stocks/{ticker}` (detail); the served `market_cap` comes from
  storage (not recomputed).
- **(unit) Risk-Off gating (code-level, J-07):** the chosen Risk-off bootstrap run yields **zero** Actionable
  under the new universe.
- **(unit) Coverage/universe consistency:** `GET /api/data` universe count == `len(resolved universe)` ==
  the count surfaced on `GET /api/methodology` (one source, no drift).
- **(browser, J-22) read flow:** on `/methodology` read the Universe-Selection rule + the three config
  thresholds; confirm the resolved size is **~400–500** and matches config; on `/data` confirm the same grown
  count; on `/stocks` confirm **many more ranked rows than before** (≫ 122).
- **(browser) regression sweep (full flows; serialize Chrome; assert live DOM/URL before each capture;
  de-dup evidence by sha256):** **J-07** (open the Risk-off run → zero Actionable), **J-02** (sector +
  Actionable filters narrow rows), **J-01** (dashboard regime + counts + breadth render), **J-06** (a named
  stock's three scores identical leaderboard↔detail), **J-16** (VCP filter → badge → detail → glossary →
  System Health by-VCP), **J-09** (by-bucket + control groups render with `n`), **J-11** (add a screened
  name → persists across restart), **J-17** (coverage symbol count grew). Full green set **J-01…J-21** stays green.

## Risks & prerequisites (verify BEFORE the costly re-seed)
1. **Network at build time (hard prerequisite).** The screen+ingest step needs outbound HTTPS to Yahoo for
   ~500 candidates (OHLCV + market cap + sector). This is a **one-shot, offline, dev-time** operation; results
   are **frozen + committed** and the boot/build loop afterward only READS them. iter-1 built the seed from
   Yahoo successfully (precedent). **If the environment cannot reach Yahoo, J-22 cannot honestly complete —
   surface an explicit failure/stall; DO NOT fabricate** (anti-goal). This is the #1 critical path.
2. **A real no-key market-cap + GICS-sector source.** The Yahoo *chart* endpoint (OHLCV) is no-key and proven;
   the **quote/quoteSummary** route for `marketCap` + `sector` can be cookie/crumb-gated. The dev MUST confirm
   a working no-key route (or an equivalent real, committed-reproducible source) **before** the full re-seed.
   Market cap = shares × price is acceptable only from **real fetched** shares-outstanding — never an estimate.
   No key may be committed (`No secrets in source`).
3. **Bootstrap-date regime flip (J-07/J-08).** Most likely regression — handle deliberately (re-verify; swap
   to a real Risk-off date in config only if needed; document).
4. **Heavy runtime.** Re-seeding ~500 names + regenerating bootstrap snapshots + forward returns over ~4× the
   universe is expensive (full backend suite is already ~14 min; walk-forward boot dominates). Expect a long
   dev+QA cycle; run pytest **once** (do not launch concurrent pytest invocations — see project memory).
5. **Count discrepancy (122 vs 158).** Goal prose says "158"; the ranked-stock universe is **122**. QA must
   assert "≫ before / ~400–500", not an exact "not 158".

## Coherence guardrails / documented assumptions
- **Universe screen reproducible & honest (critical):** membership comes from the **config-recorded screen**
  applied to a **committed, documented candidate pool** — no hand-curated list masquerading as a screen;
  failed/below-threshold candidates omitted + logged; **no fabricated bars/scores; no committed secret.**
- **Single source / no recompute (critical):** the universe is resolved **once** at build time → committed
  `universe.symbols` + per-member `Stock.market_cap`/sector + `universe.json`; the app **reads** it. The screen
  **rule + thresholds + size** are served by `/api/methodology` (thresholds live via `ref`); the **count** by
  `/api/data` — **both read the same resolved universe; neither recomputes membership or market cap.** Not a
  second computation of any existing score/return/bucket — it is the universe those engines already iterate.
- **Snapshots immutable + no-lookahead (critical):** regenerated snapshots are **create-once**, ≤ D; existing
  rows never mutated; `forward_returns` stays append-only, > D. Re-fetch re-bases adjustments → existing names'
  exact numbers may shift slightly; **acceptable because every journey asserts structural/relational properties**
  (ranking order, same-value-in-two-places, zero-Actionable-in-risk-off, a number renders, filters change rows)
  — the dev MUST **re-verify** these invariants, not assume them.
- **Risk-Off gates Actionable (critical, J-07):** re-verified at code level + in the browser on the chosen
  Risk-off bootstrap date after expansion.
- **Honest limitations preserved:** breadth + new-high/low stay **"universe-relative"**; walk-forward evidence
  stays **survivorship-biased** labelled.
- **Date grid unchanged:** only universe **width** grows — no change to `asof_cadence` / `history_years` /
  bootstrap-date **count** (a single bootstrap-date **swap** to a real Risk-off date is the only allowed change,
  and only if the expansion flips that date's regime label).
- **Blueprint:** flip the J-22 Data-Contract + journey-home rows to "built iter-7"; **no nav-skeleton change,
  no `blueprint.reapproval-requested`** (the `/research` labs J-25–J-31 — the only pending nav addition — remain
  out of scope).

## Out of scope (excluded — flag if the spec is read to ask for them)
- **J-23 / J-24** (multi-timeframe bars + chart timeframe selector); **J-25–J-31** (`/research` Factor Lab,
  Setup & Pattern Lab, volatility family, synthesis — require a new `/research` nav home + blueprint
  re-approval); **J-28** (more patterns).
- **Widening the walk-forward date grid** (`asof_cadence` / `history_years` / bootstrap-date count) — fixed.
- **Changing any scoring weight / threshold / bucket edge / decision rule** — tuning is NOT part of J-22.
- **Live Data Manager runtime fetch semantics (J-17)** beyond naturally reporting the grown coverage — do not
  alter the live-fetch/backfill job behavior.
- **Any fundamental data beyond the single market-cap reference value** needed for the screen (no P/E, earnings, etc.).
- Not GOAL_ACHIEVED after this iter — J-23…J-31 remain unbuilt; iter-7 is the data foundation that makes their
  evidence credible.
