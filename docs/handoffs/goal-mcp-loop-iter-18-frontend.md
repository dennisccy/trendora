# goal-mcp-loop-iter-18 Frontend Handoff

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

- **Stock Detail chart range control (J-10)** — a two-option segmented toggle ("Recent" ↔ "Full
  history") inline in the chart header next to the existing Regime toggle, matching the page's
  control idiom (hover/focus-visible/active states, aria-pressed, persisted like the regime toggle
  via `usePersistedToggle("trendora.detail.chartFullHistory")`). The selection only changes the
  SAME `/bars` endpoint's `range` param — the page never slices or recomputes a series
  client-side. Loading skeleton shows on every range switch (state resets to loading on refetch).
- **Honest depth caption** — the chart header now reads
  "N bars · as of DATE · history since FIRST_AVAILABLE_DATE (· older bars weekly-sampled)" from the
  new payload keys, so a long-tenured name discloses its real 1996-era first bar even in the
  bounded default view, and a post-IPO name (ARM/COIN/HOOD) honestly shows its short real history.
- **/data staleness surfaces (J-12)** — the J-94 Universe-resolution diagnostic gains the fourth
  reason card ("Stale series", threshold-driven definition from the served
  `thresholds.max_staleness_days`; grid widened to 5 columns), the J-96 membership-timeline table
  column becomes "Excl. hist / stale / price / liq", and the resolved-universe hint copy names the
  freshness gate.
- **api.ts** — `fetchStockBars` gains the optional `range` arg; `BarsResponse` gains
  `range` / `first_available_date` / `window_start` / `downsampled`; `UniverseDiagnostic` +
  `MembershipTimelinePoint` excluded maps gain `stale_series`; thresholds gain
  `max_staleness_days`.

## Files Changed

- `apps/frontend/app/stocks/[ticker]/page.tsx` — ChartRangeControl component + caption + range state
- `apps/frontend/lib/api.ts` — types + fetch param (all additive)
- `apps/frontend/app/data/page.tsx` — staleness reason card, timeline column header/cell, hint copy
- `apps/frontend/lib/membership-timeline-view.test.ts` — fixture gains `stale_series: 0`

## Tests Run

Command: `cd apps/frontend && npx --offline tsx lib/<file>.test.ts` (each) + `npx tsc --noEmit`
Result: 8/8 test files passed; typecheck clean.

## Known Issues

- ~~Stale "real ledger" mirror comments in `lib/evidence.test.ts` + `lib/factor-lab-evidence.test.ts`~~
  — **RESOLVED in fix-mode dispatch 2 (2026-07-03 03:44Z):** both files gained an `iter-18 NOTE`
  header declaring every mirror fixture a self-contained SYNTHETIC payload on the RETIRED pre-swap
  basis, and every "mirrors the REAL ledger line N" comment now reads "RETIRED … (synthetic
  post-reset)". No behavioral edits; suites re-verified green (8/8 + `tsc --noEmit`, independently
  re-run by the iter-18 review). The RUNNING app renders only the regenerated `GET /api/evidence`
  rows (all honestly "Not yet proven"/FAIL — nothing Proven anywhere until a claim re-certifies).
- Evidence-status components (`evidence-status-badge`, ClaimRow, proof panels) are structurally
  untouched — the regenerated content flows through the same single-source payload.
- Browser verification of the chart range control + staleness surfaces is handed off to the
  pipeline's QA stage (canonical browser-qa lane — J-10/J-11/J-12 + J-01..J-05 fresh pixels).
