**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-6 (J-20 chart-through-latest, J-21 backtest leadership returns)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 6 — full depth, target journeys J-20, J-21
- **Snapshot audited:** `git diff 5f0e6941a1f17883e109f1acebeb99629f00ebe9` (uncommitted working tree)
- **Auditor scope:** Data Contract drift + Information Architecture drift vs `state/blueprint.md`. (Functional correctness is the reviewer's/QA's domain — not re-judged here.)

Source files changed this iter: `api/stocks.py`, `engine/forward_testing.py`, `engine/prices.py` (backend) + 3 test files; `app/backtest/page.tsx`, `app/stocks/[ticker]/page.tsx`, `components/price-chart.tsx`, `lib/api.ts` (frontend). The blueprint was updated additively to register the two new values.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) — PASS

**J-20 — chart full-path-through-latest (`bars_through_latest` + `?through=latest`):** No violation.
- Extends the **existing** "Price / MA / volume series" contract row served by the **same** canonical endpoint `GET /api/stocks/{ticker}/bars` (`api/stocks.py:79`). The forward extension is an explicit opt-in; the **default** contract (no `through`) is byte-identical at ≤ D (`api/stocks.py:78-79` branches on `through == "latest"`; `is_forward`/`latest_date` added only in full-path mode). NOT a new canonical value.
- **No-lookahead seam holds (source-asserted).** `bars_through_latest` (`prices.py:83`) is referenced **only** by the chart endpoint + tests — grep confirms zero references in `scoring.py`/`scanner.py`/`patterns.py`, and a dedicated source-seam test (`tests/test_bars.py:196` `test_bars_through_latest_not_in_scoring_path_source_seam`) enforces it. The post-D bars/MA never feed a score/bucket/setup/VCP/ranking — those keep reading the immutable snapshot row via `/api/stocks` + `/api/stocks/{ticker}`.
- The ≤ D MA values are byte-identical with/without the forward extension (trailing `sma_series` depends only on prior closes; `api/stocks.py:84-89` comment + test `test_bars_through_latest_ma_le_d_region_matches_default`). No duplicate computation, no non-canonical source.
- Frontend (`stocks/[ticker]/page.tsx:280`) passes `"latest"` to the chart endpoint; scores/setup/VCP/invalidation still read `fetchStock` (the ≤ D snapshot) unchanged. `price-chart.tsx` is pure rendering off the payload's `is_forward` flag — plots the **server** `ma`, recomputes nothing.
- Registered in the blueprint Data Contract (the "Price / MA / volume series" row note updated, `blueprint.md:132`).

**J-21 — backtest leadership realized returns (`_leadership_returns`):** No violation.
- A pure **read-only projection** (`forward_testing.py:464`) over `ret_by_symbol`, which is built directly from the stored `ForwardReturn` rows (`forward_testing.py:674-675` `ret_by_symbol = {fr.symbol: fr.realized_return …}`) — the **same** stored observations `compute_run_scorecard`/`_attribution_slices` already read. It takes no `Session`, issues no query, recomputes no return. Satisfies coherence invariant #9 (Attribution is read-only).
- Served on the **existing** `GET /api/backtest` riding `scorecard.by_horizon[*].leadership_returns` (`forward_testing.py:716`), mirroring how `attribution` rides each entry. **No new endpoint** (`git diff` of `api/` shows zero new `@router` decorators; `api/backtest.py` unchanged).
- Config-sourced, no magic numbers: sectors via `cfg.etfs.sector`, themes via `cfg.themes`, cohort via `cfg.universe.symbols` (all verified to resolve to real config values). Honest NA — `mean_return: None` / `n: 0` when a (row, horizon) lacks a stored return; nothing fabricated.
- Frontend (`backtest/page.tsx`) joins these by key (`sector_etf` → `/api/sectors`, `slug` → `/api/themes`, `ticker` → `/api/stocks`) into Maps and renders via the **pre-existing** pure `Return` formatter (`@/components/forward-return`). No client-side return math.
- Registered in the blueprint Data Contract as a new read-only-slice row (`blueprint.md:140`).

No unregistered-value WARN: both new values were added to the Data Contract this iter. No canonical-compute module (`scoring`/`scanner`/`patterns`/`buckets`/`regime`/`snapshot_serving`) was touched — the work is purely a display accessor + a read-only projection.

## Step 2 — Information Architecture check — PASS

- **0 new routes/pages** (ui-surface-map + diff agree). J-20 refines the **existing** `/stocks/[ticker]` home (row-reached from `/stocks`, ≤ 2 clicks); J-21 refines the **existing** `/backtest` home (top-level sidebar, 1 click). No parallel shell, no duplicate home, no hidden feature.
- **Nav skeleton unchanged.** The blueprint's nav code block is not in the diff; the blueprint change is additive only (two journey-home rows + a NEW-WAVE documentation comment). No `blueprint.reapproval-requested` written — correct, since the iter introduces no skeleton entry (the `/research` home for later wave members is explicitly deferred).
- **J-18 (exactly one date selector) preserved.** The `viewHorizon` state is **lifted** into `BacktestResults` (`backtest/page.tsx:172`); the old `BacktestAttributionSection` that previously held it is **deleted**. There is still exactly one horizon **VIEW** selector — `onChange={setViewHorizon}` only re-selects an already-fetched `by_horizon` row (no refetch, no date param, no date state). It now re-points both Return Attribution and the three leadership return columns. No `BacktestDatePicker`-style control reappears; the global as-of switcher still owns the date.
- Section reorder (As-of summary → scorecard → Return Attribution → Top Sectors/Themes/Ranked Cohort) is a layout change within the same home — matches the spec; not a coherence concern.

## Step 3 — Subjective observations (advisory) — none blocking

- Positive: the forward region uses design-system CSS-var tokens (`--text-faint`, `--border-strong`, `--warn` in `price-chart.tsx:29-31`) — no ad-hoc hex; NA rendered honestly as "—"; consistent "Fwd {horizon}d" column labels. No label/format drift between the new columns and existing surfaces was observed.

---

## Conclusion

No objective Data-Contract or Information-Architecture violations. Both new values reuse a single canonical source (J-20 extends one endpoint display-only with a source-asserted no-lookahead carve-out; J-21 is a read-only projection of the already-stored `forward_returns` on the existing endpoint), both refine existing nav homes with no skeleton change, and the single-date-selector invariant is preserved by lifting (not duplicating) the horizon view selector. **COHERENCE-PASS** — no remediation required; nothing queued for the next iteration to tidy.
