# Phase goal-i_can_see_the_wealthy_future-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8835` with a built snapshot DB (walk-forward backfill complete)
- Frontend running at `http://localhost:3835`
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/stocks`
   - **Expect:** Heading `Stocks`; a filter row with `Sector`, `Setup`, and `VCP` dropdowns; a `<n> / <total>` count; table headers `# Ticker Sector Leadership Entry Quality Risk Setup Reason`.

2. In the `VCP` dropdown choose `VCP only`
   - **Expect:** The table shrinks to only rows that carry a teal `VCP` badge in their Setup cell; the left number of `<n> / <total>` drops; the right number (total) is unchanged.
   - **Broken looks like:** the count doesn't change, or rows without a teal `VCP` badge remain.

3. Hover the teal `VCP` badge on the first row (wait ~1s for the tooltip)
   - **Expect:** A tooltip with a plain-language reason, a `Pivot $<number>.` fragment, and an invalidation sentence — no `undefined` / `Pivot $.`.

4. Click that first ticker to open its detail page (`/stocks/<TICKER>`)
   - **Expect:** A teal `VCP` badge next to the setup-status badge in the header card, AND a card titled `VCP — Volatility Contraction Pattern` showing the reason, `Pivot (breakout level)` with a `$` value, the invalidation note (amber), and `Contractions` chips.

5. Confirm the pivot matches step 3
   - **Expect:** The `Pivot (breakout level)` value on the detail card equals the `Pivot $<number>` you saw in the leaderboard tooltip (same cents) — proving leaderboard and detail serve one stored value.

6. Go back to `http://localhost:3835/stocks`, set `VCP` to `Non-VCP`, click the first ticker
   - **Expect:** On its detail page there is NO teal VCP badge, and the VCP region reads `No VCP pattern detected.` with no pivot/invalidation numbers (nothing fabricated).

7. Back on `http://localhost:3835/stocks`, set `VCP` to `All`, then pick a specific `Sector` (e.g. `Technology`)
   - **Expect:** Rows narrow to that sector and the count updates; ranking order is unchanged — the VCP filter did not disturb the existing Sector/Setup filters.

8. Open `http://localhost:3835/system-health`
   - **Expect:** The dashboard renders with a `Survivorship bias` banner and a panel titled `Forward return: VCP vs non-VCP` showing two rows (`VCP`, `non-VCP`), each with a mean return and `n=<count>`; `n < 30` shows a `⚠`, an empty cohort shows `—`.

9. On `/system-health` click a different `Horizon` button (e.g. `60d`)
   - **Expect:** Every panel — including `Forward return: VCP vs non-VCP` and the existing `by score bucket` / `Excess vs benchmarks` / `by setup type` / `by market regime` / `Control-group` panels — updates its numbers without error.

---

## What "Working Correctly" Looks Like

- `/stocks` has a working `VCP` filter and teal `VCP` badges with explanatory tooltips on flagged rows.
- A flagged stock's detail page shows the dedicated VCP card with a pivot, invalidation note, and contraction chips; a non-flagged stock honestly says `No VCP pattern detected.`
- The pivot/invalidation shown on the detail page is identical to the leaderboard tooltip.
- `/system-health` has a `Forward return: VCP vs non-VCP` panel with sample sizes and honest ⚠/— markers.

## Common Issues

- **"Backend unavailable" card on `/stocks` or `/system-health`** → backend not running on :8835, or CORS not set to the frontend origin. Start backend with `CORS_ORIGINS=http://localhost:3835`.
- **No teal `VCP` badge on any row, and `VCP only` yields the empty-state** → the latest snapshot honestly flagged no VCP names; this is acceptable (verify the empty-state in step 2 and the not-detected state in step 6 instead). Do NOT treat an honest empty-state as a failure.
- **`undefined` / `$undefined` in the VCP card or tooltip** → the API row is missing the `vcp` block → check `GET http://localhost:8835/api/stocks` returns a `vcp` object per row; report to the developer.
- **`Forward return: VCP vs non-VCP` panel missing** → `by_vcp` not in `GET /api/system-health`; report to the developer.
- **`/system-health` shows "No forward-tested evidence yet"** → walk-forward backfill not finished; wait or pick a shorter horizon.

End of guide.
