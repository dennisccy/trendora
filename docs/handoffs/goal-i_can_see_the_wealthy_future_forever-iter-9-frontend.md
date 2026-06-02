# goal-i_can_see_the_wealthy_future_forever-iter-9 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The product's pattern vocabulary grows from one detected pattern (VCP) to three. The two new patterns
(`pullback_to_rising_dma`, `flat_base_breakout`) are surfaced everywhere VCP already is — re-displaying
server values only, never recomputing a flag/score/return client-side (single source of truth).

- **Stock Leaderboard (`/stocks`):**
  - The old "VCP" filter (`All / VCP only / Non-VCP`) is generalized into one **"Pattern"** `<Select>`
    with an optgroup per pattern: each pattern has a `<name> only` and a `Not <name>` option. Driven by
    a small `PATTERNS` registry — adding a pattern is one entry; the filter, badges, and tooltips all
    read it (config-driven UI vocabulary). Filtering is pure client-side re-display of
    `row.<name>.flagged`.
  - Each flagged stock renders a teal accent **badge** per pattern (`VCP`, `Pullback`, `Flat base`) with
    a hover tooltip carrying the server-built reason + pivot + concrete invalidation note (verbatim),
    plus an info tooltip with the pattern's glossary meaning (from the config catalog).
  - Empty-state copy is honest and pattern-aware (e.g. "No Pullback to rising DMA-flagged name is
    currently shown … no rows are fabricated").
- **Stock Detail (`/stocks/[ticker]`):**
  - The header shows a badge per flagged pattern alongside the setup status.
  - A dedicated **pattern card** (reason + pivot + invalidation) renders for each flagged new pattern.
    The existing VCP card is unchanged (still always shown, incl. its not-detected state + contractions).
- **Methodology / Glossary (`/methodology`):** the two new pattern cards render **automatically** from
  the config-backed catalog (the page already maps `entries` generically) — meaning + config thresholds
  (read live) + worked example. Only the page subtitle was generalized from "the VCP pattern" to
  "detected price pattern".
- **System Health (`/system-health`):** two new **breakdown panels** —
  "Forward return: Pullback-to-rising-DMA vs not" and "Forward return: Flat-base breakout vs not" —
  reuse the existing `BreakdownPanel`, each showing the flagged vs non-flagged cohort mean return with
  sample size `n` and honest NA below `min_sample`.

## Files Changed

- `apps/frontend/lib/api.ts` — `PullbackToRisingDma` + `FlatBaseBreakout` interfaces (mirror `Vcp`);
  `StockRow` extended with the two pattern fields; `ForwardPullbackRow` + `ForwardFlatBaseRow`;
  `SystemHealthResponse` gains `by_pullback_to_rising_dma` + `by_flat_base_breakout`.
- `apps/frontend/app/stocks/page.tsx` — `PATTERNS` registry + `patternTitle`; `pattern` filter state +
  optgroup `<Select>`; per-pattern badge/tooltip loop; pattern-aware empty state.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `NEW_PATTERNS` registry + `patternTitle`;
  `PatternBadge` + `PatternCard` components; header badges + cards for flagged new patterns.
- `apps/frontend/app/system-health/page.tsx` — two new `BreakdownPanel`s.
- `apps/frontend/app/methodology/page.tsx` — subtitle copy generalized (cards auto-render).

## Design System Compliance

- Reused existing components only: `Badge` (accent variant for all pattern badges, matching VCP),
  `Select` (filter), `InfoTooltip` (glossary tooltips), `EntryCard` (auto glossary cards),
  `BreakdownPanel` + `Return`/`SampleSize` (System Health). No new component families.
- Palette tokens only (`--accent` teal for pattern badges; `--pos`/`--neg` for returns; `--warn` for
  low-sample/NA). Monospace tabular-nums for all numbers. Layout unchanged (dense dark workstation).
- States handled: flagged vs not (badge only when flagged), honest empty filter result, low-sample NA
  with `n`, and the existing "Backend unavailable" error cards.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: PASS — "Compiled successfully", types valid, all 13 routes generated.
(UI behaviour is verified by the browser-qa-agent, not a unit suite — per project-template.)

## Known Issues

- The detail-page pattern card's pivot label is generic ("Pivot (breakout level)"); for the pullback
  pattern this is the recent high (resumption level), for the flat base it is the base high.
- The browser-qa-agent should de-dup screenshots by sha256 and assert filtered row count / badge
  presence in the DOM for each pattern filter (per the iter-9 process guardrails).
