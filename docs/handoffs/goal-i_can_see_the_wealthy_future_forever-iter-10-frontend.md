# goal-i_can_see_the_wealthy_future_forever-iter-10 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete
**Target journey:** J-25 (Factor Lab)

## What Was Built (UI)

- **New route `/research` — the Research home, rendering the Factor Lab** (`apps/frontend/app/research/page.tsx`).
  Reached in ≤2 clicks from the new sidebar entry. Layout modeled on `/system-health` (dark analytical
  workstation; `tabular-nums` numbers; `--pos`/`--neg`/`--warn` palette colour grading only).
  - **Factor selector** (`data-testid="factor-select"`) — a `Select` (styled native `<select>`) whose
    `<option>`s are built from the server payload's `factors` catalog. **Config-driven**: a factor added
    to `config.research.factor_lab.factors` appears here with NO frontend edit (the iter-9 lesson).
  - **Horizon selector** (`data-testid="horizon-select"`) — a button group built from the payload's
    `horizons` (config-driven), one button per horizon (`1d/5d/10d/20d/60d`), `aria-pressed` on the active.
  - **Decile table (D1…D10)** — columns: Decile, Factor range, **Mean fwd return** (raw), **Risk-adjusted
    (downside)**, each colour-graded by sign with its sample size `n`. A low-sample (`n < min_sample`) or
    empty cell renders an explicit **"NA"** + the `n` (never blank, never a fabricated number). Scrolls
    horizontally < ~640px.
  - **Rank-IC card** (`data-testid="rank-ic-value"`) — the Spearman rank-IC as a large signed number
    (green positive / red negative / muted NA) + `n` + a plain-language one-liner interpreting the sign.
  - **Caveat banner** — the survivorship-bias label + the descriptive/universe-relative caveat, rendered
    verbatim from the payload.
  - **States** — loading skeleton; empty (`n_total === 0`) EmptyState; error ("Backend unavailable", no
    fabricated values). 
  - **No date control** (J-18) — the page imports no `useAsOf`/as-of state; its only controls are factor
    + horizon. It is a cross-date aggregate (like System Health).
- **Sidebar** (`apps/frontend/components/sidebar.tsx`) — additive `{ href: "/research", label: "Research",
  icon: Microscope }` NavItem, placed between System Health and Watchlist. No other nav entry changed.
- **API client** (`apps/frontend/lib/api.ts`) — `FactorLabResponse` / `FactorLabFactor` / `FactorDecileRow`
  / `RankIC` types + `fetchFactorLab(factor?, horizon?, signal?)`. Re-formats server values only — no
  score/return/factor is computed client-side. The risk-adjusted column + rank-IC use a unitless
  `fmtRatio` (sign + 2 decimals), distinct from the percent `fmtPct` used for returns.

## How a user reaches it
1. Click **Research** in the left sidebar → `/research` loads the Factor Lab.
2. Pick a **factor** from the dropdown and a **horizon** from the button group.
3. Read the **decile table** (D1 lowest factor value → D10 highest; raw mean return + downside
   risk-adjusted, each with n) and the **rank-IC** (signed + n). Changing factor or horizon re-points
   both to the server's values (no client recompute).

## Files Changed
- `apps/frontend/app/research/page.tsx` — **new**: Factor Lab page (selectors + decile table + rank-IC + caveats; no date control).
- `apps/frontend/components/sidebar.tsx` — additive Research NavItem (+ `Microscope` icon import).
- `apps/frontend/lib/api.ts` — Factor-Lab types + `fetchFactorLab()`.

## Tests Run
Command: `cd apps/frontend && npm run build`
Result: compiled successfully; typechecked all 14 routes. `/research` = 5.41 kB / 118 kB First-Load JS.
Live: the page's data source `GET /api/research/factor-lab` was curl-verified on :8835 (200, full decile
table + rank-IC, no date key; 422 on bad factor/horizon; 503 with no data) — see the dev handoff.

## Known Issues (UI)
- **NA/low-sample decile cells are not observable on the committed seed.** Every catalogued factor has
  ~1218 observations (~121 per decile, all > `min_sample` 30) at every horizon, so the decile cells render
  real numbers, not NA. The NA rendering (`DecileValue` → "NA" + n when `low_sample`/empty) is correct and
  unit-tested on the backend; it simply isn't triggered by switching controls on this seed. **Browser QA:
  do not flag the absence of an NA cell as a defect.**
- Decile means are non-monotone and the rank-IC is near zero on the seed — this is the honest descriptive
  finding (the factors don't strongly sort short-horizon forward returns in this small universe), and the
  colour grading reflects it faithfully.

## Notes for browser QA (J-25 + regressions)
- **Discoverability:** sidebar shows **Research**; clicking it loads `/research` (≤2 clicks).
- **Config-driven dropdown:** assert the `factor-select` `<option>` values equal the server `factors`
  catalog keys (`leadership_score, entry_quality_score, risk_score, rs_spy_3m, ma_stack, high_proximity,
  up_down_vol, atr_pct`) — they come from the payload, not a hardcoded list.
- **Re-point:** change the factor and the horizon and assert the decile table / rank-IC values change
  (server values; ground before/after on distinct DOM reads + the network response, not one screenshot
  pair; serialize Chrome access with the `qa` agent and de-dup evidence by sha256 — iter-6 lesson).
- **Labels:** the survivorship + descriptive/universe-relative caveat banner is visible.
- **J-18 regression:** assert `/research` has **no** date/as-of selector (only factor + horizon).
- **J-09 / J-01 regressions:** `/system-health` still renders its by-bucket/excess/control-group evidence;
  `/` + the full sidebar (now with Research) still render.
