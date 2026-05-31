# goal-i_can_see_the_wealthy_future-iter-11 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built (UI)

All three surfaces are **existing** Information-Architecture homes — **no navigation/sidebar change**,
so no blueprint reapproval this iteration. Every value is re-formatted from the API; nothing is
recomputed client-side (the VCP filter is a pure client-side re-display of `row.vcp.flagged`).

- **`/stocks` (Stock Leaderboard)**
  - New **VCP filter** `Select` (All / VCP only / Non-VCP), parallel to the existing Sector and Setup
    filters. Narrows the already-fetched rows on `row.vcp.flagged` (no re-sort, no recompute). The
    `n / total` count reflects the filtered view; "VCP only" with zero matches shows the existing
    styled empty-state ("No VCP-flagged name … No rows are fabricated …").
  - New compact teal **VCP `Badge`** in the Setup cell of each flagged row, sitting **alongside** the
    setup-status badge. Its `title` tooltip carries the server-built reason + pivot + invalidation note
    (rendered verbatim — never assembled client-side).
- **`/stocks/[ticker]` (Stock Detail)**
  - The header card shows the **VCP badge** next to the setup status when flagged.
  - A dedicated **"VCP — Volatility Contraction Pattern"** card shows the reason, the **Pivot (breakout
    level)**, the **Invalidation** sentence (rendered verbatim), and the contraction-depth chips. When
    not flagged it shows an explicit "No VCP pattern detected." — never a fabricated pivot.
  - The values are the SAME stored row the leaderboard serves (J-06 — verified byte-identical).
- **`/system-health`**
  - New **"Forward return: VCP vs non-VCP"** breakdown panel (reusing the shared `BreakdownPanel` +
    `Return`/`SampleSize` formatters) alongside the existing by-setup / by-regime panels. Each cohort
    shows its mean return + `n`, flagged ⚠ when below `min_sample`, em-dash NA when no observation.

## Files Changed

- `apps/frontend/lib/api.ts` — added `Vcp` interface + `vcp: Vcp` on `StockRow`; `ForwardVcpRow` +
  `by_vcp: ForwardVcpRow[]` on `SystemHealthResponse`. No new fetcher (VCP rides the existing
  `/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`).
- `apps/frontend/app/stocks/page.tsx` — VCP filter `Select`, `vcpTitle()` tooltip helper, VCP badge in
  the Setup cell, VCP-aware empty-state, filter wired into the `visible` memo.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `VcpBadge` (header) + `VcpCard` (pivot/invalidation/
  contractions or explicit not-detected), imported `Vcp` type.
- `apps/frontend/app/system-health/page.tsx` — `by_vcp` `BreakdownPanel` in the grid.

## Visual / Design Conformance

- shadcn `Select` matches the existing sector/setup filters; the VCP `Badge` uses the `accent`
  (teal `--accent`) variant — distinct from setup-status colour variants, reading as "explained +
  separate from the verdict", not a hype banner.
- Palette/spacing/typography tokens only; numbers monospace/tabular; low-sample `n < min_sample`
  flagged with the `--warn` token. Loading skeletons, the backend-unavailable card, and empty-states
  are unchanged and still handled.

## Tests / Verification

- `cd apps/frontend && npm run build` — **clean**; typecheck passes with the new `vcp` field on
  `StockRow`; all 11 routes compiled.
- Live browser walkthrough (frontend `next dev` on 3835 → backend 8835), distinct PNGs captured in
  `reports/evidence/goal-i_can_see_the_wealthy_future-iter-11/`:
  - `01-leaderboard-vcp-filtered.png` — VCP filter narrows 122 → the 4 flagged rows (STX/TSLA/TSM/ORCL)
    with VCP badges; ranks 4/37/47/56 show VCP is independent of leadership rank.
  - `02-detail-STX-vcp.png` — STX detail: VCP badge beside "Extended" + VCP card (pivot $905.39,
    invalidation $816.98).
  - `04-detail-ORCL-vcp.png` — ORCL detail: distinct pivot $205.00, invalidation $187.92 (proves the
    card generalizes across names).
  - `03-system-health-by-vcp.png` — VCP +3.18% (n=27 ⚠) vs non-VCP +2.01% (n=1191) @ 20-day.

## Known Issues

- None specific to the frontend. The VCP cohort's low sample size (n=27) is surfaced honestly via the
  shared ⚠ low-sample marker. `/methodology` (J-12) is intentionally deferred to the next iteration.
