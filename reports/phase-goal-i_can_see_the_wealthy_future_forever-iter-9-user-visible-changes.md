# Phase goal-i_can_see_the_wealthy_future_forever-iter-9 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

The product's detected-pattern vocabulary grows from one (VCP) to three. Everywhere VCP appeared, two new patterns now appear alongside it — **Pullback to rising DMA** and **Flat-base breakout**.

- Users can now **filter the stock leaderboard by any of three detected patterns** at `/stocks` using the new **"Pattern"** dropdown — choosing `<pattern> only` or `Not <pattern>` for VCP, Pullback, or Flat base (previously the filter only offered All / VCP only / Non-VCP).
- Users can now **see Pullback and Flat-base badges on flagged stocks** in the `/stocks` leaderboard, each with a hover tooltip carrying the server-built reason, pivot, and invalidation note, plus an info tooltip with the pattern's glossary definition.
- Users can now **read a per-pattern card on a stock's detail page** (`/stocks/[ticker]`) for each newly flagged pattern, showing reason + pivot + invalidation, in addition to header badges next to the setup status.
- Users can now **see how each new pattern's cohort performs** on `/system-health` via two new forward-return breakdown panels: "Forward return: Pullback-to-rising-DMA vs not" and "Forward return: Flat-base breakout vs not".
- Users can now **look up the definition and config thresholds for the two new patterns** in the `/methodology` glossary — the cards render automatically from the catalog with meaning, live thresholds, and a worked example.

---

## What Changed in the Visible UI

- **`/stocks` (Stock Leaderboard):** The old "VCP" filter `<Select>` (All / VCP only / Non-VCP) is replaced by a generalized **"Pattern"** `<Select>` with an option group per pattern (`<pattern> only` / `Not <pattern>`). Flagged rows now render one teal accent badge per matching pattern (`VCP`, `Pullback`, `Flat base`), each with reason/pivot/invalidation and glossary tooltips. The empty-state message is pattern-aware (e.g. "No Pullback to rising DMA name…").
- **`/stocks/[ticker]` (Stock Detail):** The header now shows a badge per flagged pattern next to the setup status, and a dedicated pattern card (reason + pivot + invalidation) renders for each flagged new pattern. The existing VCP card is unchanged.
- **`/system-health`:** Two new `BreakdownPanel`s were added below the existing VCP panel, each showing flagged vs non-flagged cohort mean forward return with sample size `n` and honest NA when below the minimum sample.
- **`/methodology`:** Two new glossary cards (Pullback to rising DMA, Flat-base breakout) auto-render from the config catalog. The page subtitle was generalized from "the VCP pattern" to "detected price pattern".

---

## What Old Behavior Changed

- **`/stocks` pattern filter:** previously a VCP-only filter with three fixed choices (All / VCP only / Non-VCP). Now a registry-driven dropdown covering all three patterns. Re-verify that selecting "VCP only" / "Not VCP" still filters identically to before.
- **`/stocks` badges:** previously a single VCP badge appeared on flagged rows. Now a flagged row may show up to three pattern badges. Re-verify VCP badge appearance/tooltip is unchanged.
- **`/methodology` subtitle:** copy changed from VCP-specific to generic "detected price pattern" wording. VCP card content itself is unchanged.

---

## Not Visible Yet

- **`/research` labs (J-25–J-31):** the `/research` navigation home was front-loaded into the blueprint by the decomposer, but no `/research` code ships in this iteration — there is no functioning research page yet.
- **Universe-expansion journeys (J-22/23/24):** remain blocked by external data limits (Yahoo 429); no UI for an expanded universe.
- Backend forward-test cohorts below `walk_forward.min_sample` show NA + `n` rather than a number — this is intentional honesty, not a missing feature.
