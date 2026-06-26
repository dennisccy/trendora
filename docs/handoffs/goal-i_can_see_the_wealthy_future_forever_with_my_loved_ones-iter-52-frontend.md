# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The Factor Lab (`/research/factor-lab`) became an **all-horizon, risk-aware factor screen**: a user sees
every catalog factor's top-decile forward-return edge AND its paired downside (max-drawdown) at all five
horizons (1/5/10/20/60d) in one table — with no horizon-picking step — then can expand any factor to its
full D1…D10 decile grid (same paired columns), and drill any cell into its exact cohort.

- **Horizon `<select>` removed.** The page no longer fetches per-horizon; it fires `?all=true` once and
  renders all horizons at once. The As-of vs All-history mode toggle (single global as-of, J-18) remains.
- **All-factors table.** Columns: Factor · Family · Rank-IC (Nd) · N · Risk-adjusted (Nd) · then per
  horizon a **Fwd {h}d** + **MDD {h}d** pair (the factor's top-decile D10 cohort). Rank-IC / N /
  risk-adjusted are fixed at the config default horizon (20d), relabelled with it. Every numeric column is
  client-side sortable NA-last — including each per-horizon `fwd:`/`mdd:` column (a pure view transform;
  recomputes / refetches nothing). Default sort: rank-IC descending.
- **Expandable all-horizon decile grid.** Clicking a factor row reveals a grid: rows D1…D10, columns =
  factor range (at the default horizon) then, per horizon, a paired **Fwd {h}d** + **MDD {h}d** cell. Each
  forward-return cell carries the per-`(factor, horizon, decile)` `N=` chip (opens `/research/samples` in a
  new tab for that exact cohort, count-coherent — its total equals the chip n, carries the `?asof` scope).
- **Colour grading.** Forward-return cells use the existing return tokens (`returnClass`/`fmtPct`);
  max-drawdown cells colour-grade via the existing `lib/mdd-color` severity scale (`mddClass`/`fmtMdd`) —
  design tokens only, no hardcoded hex. A deeper drawdown reads more severe.
- **Honest states.** Loading skeleton (`LabSkeleton`), backend-unavailable card (`ResearchError`), empty
  state (`EmptyState`), and explicit muted **NA** for any low-sample (`n < min_sample`) / empty /
  null-value cell — never a fabricated number. A horizon with no observations (or no stored drawdown)
  renders NA + n, never a fabricated bucket.

## Files Changed

- `apps/frontend/lib/api.ts` -- `FactorDecileRow.mean_max_drawdown`; new `FactorHorizonDeciles`;
  `FactorTableRow.by_horizon` (replaces `deciles`); `FactorLabAllResponse` drops `horizon`;
  `fetchFactorLabAll(asof?, signal?)` (drops the horizon param).
- `apps/frontend/app/research/_labs.tsx` -- `FactorLabPage` (selector removed); `FactorsTable` (paired
  all-horizon columns + per-horizon NA-last sort keys + default-horizon labels); `FactorRows` +
  `TopDecileCell` (top-decile paired cells); `DecileTable` rebuilt as the all-horizon paired decile grid
  with `DecileReturnCell` (value + `N=` chip) and `DecileMddCell` (mdd-color). The shared `HorizonSelector`
  component is retained (still used by other research labs).

## Tests Run (frontend)

Command: `cd apps/frontend && node_modules/.bin/tsc --noEmit`
Result: EXIT 0 (TypeScript typecheck clean).

Live: `scripts/start-frontend.sh` (port 3255) compiles and serves `/research/factor-lab` -> `http=200`
against the live backend (port 8255). Both servers stopped after verification.

## Known Issues

- No new frontend unit test added: there is no pre-existing factor-lab component test harness, and the
  box's `node lib/*.test.ts` runner errors `ERR_UNKNOWN_FILE_EXTENSION` (Node 22 TS type-stripping not
  enabled). The per-horizon sort, paired columns, and count-coherence are covered by backend byte-identity
  tests + live HTTP checks; visual behaviour is verified by in-iteration browser-QA.
- The all-factors table is intentionally wide (5 + 5 horizon columns plus the default-horizon stats); the
  Card scrolls horizontally (`overflow-x-auto`) rather than dropping columns, per the plan.
- Per-horizon decile factor ranges (membership differs per horizon) are surfaced on each return cell's
  hover title; the visible "Factor range" column shows the default-horizon range.
