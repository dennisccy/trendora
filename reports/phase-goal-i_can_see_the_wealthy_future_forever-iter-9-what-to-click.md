# Phase goal-i_can_see_the_wealthy_future_forever-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running on `http://localhost:8000` with the DB regenerated (so rows carry the new pattern flags)
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/stocks` in your browser
   - **Expect:** The "Stocks" leaderboard loads with a ranked table and a filter bar showing three dropdowns: "Sector", "Setup", and "Pattern". No "Backend unavailable" card.

2. Open the "Pattern" dropdown
   - **Expect:** Options grouped as "VCP" (VCP only / Not VCP), "Pullback to rising DMA" (… only / Not …), and "Flat-base breakout" (… only / Not …). Three patterns, two modes each.

3. Select "Pullback to rising DMA only" in the "Pattern" dropdown
   - **Expect:** The `<visible> / <total>` counter on the right shrinks. Every remaining row shows a teal "Pullback" badge in the Setup column. (If zero rows qualify, you instead see a card "No stocks match these filters" naming "Pullback to rising DMA-flagged" — that is also correct, nothing is fabricated.)

4. Hover the "Pullback" badge on the first row (move on to step 5 if the empty state showed in step 3 — select "Flat-base breakout only" first to surface a flagged row)
   - **Expect:** A tooltip appears with plain-language reason text, usually a "Pivot $<number>." fragment and an invalidation note. Not "undefined" or blank.

5. Click the ticker symbol of a flagged row to open its detail page
   - **Expect:** URL becomes `/stocks/<TICKER>`. The header card shows the setup-status badge with a teal "Pullback" (or "Flat base") badge beside it. Further down, a dedicated card titled by the pattern shows the reason, a "Pivot (breakout level)" `$<number>`, and an "Invalidation" note. The "VCP — Volatility Contraction Pattern" card is still present.

6. Navigate to `http://localhost:3835/methodology`
   - **Expect:** Scrolling the glossary, you find a "Pullback to rising DMA" card AND a "Flat-base breakout" card, each with a teal "Pattern" chip, a meaning paragraph, a "Thresholds" list with real numbers, and an "Example:" line. The subtitle reads "What every setup status and detected price pattern mean…" (generic, not VCP-specific).

7. Navigate to `http://localhost:3835/system-health`
   - **Expect:** Among the breakdown panels you find "Forward return: Pullback-to-rising-DMA vs not" and "Forward return: Flat-base breakout vs not", each below the existing "VCP vs non-VCP" panel. Each shows two cohort rows with a mean return and a sample size `n`; low-sample cohorts show NA / a ⚠ marker, never a made-up number.

8. Back on `http://localhost:3835/stocks`, set the "Pattern" dropdown to "VCP only", then "All patterns"
   - **Expect:** "VCP only" still filters to VCP-flagged rows with the "VCP" badge unchanged; "All patterns" restores the full list (`<total> / <total>`). This confirms the old VCP behavior did not regress.

---

## What "Working Correctly" Looks Like

- The `/stocks` leaderboard shows up to three distinct teal pattern badges (VCP, Pullback, Flat base) on flagged rows, each with a working hover tooltip.
- The "Pattern" dropdown filters the row list live, and the `<visible> / <total>` counter tracks it.
- `/methodology` shows three pattern cards total; `/system-health` shows three pattern forward-return panels total.
- Sample sizes (`n`) appear everywhere a forward return does; below-minimum cohorts read NA, not a fabricated number.

## Common Issues

- **Blank page / "Backend unavailable" card:** Confirm the backend is running — `curl http://localhost:8000/api/stocks` should return JSON.
- **Pattern badges/tooltips missing but rows present:** The DB may not have been regenerated with the new flags, or the `/methodology` catalog fetch failed (badge tooltips degrade gracefully — the badge still shows, only the info-icon definition disappears).
- **New panels missing on System Health:** The forward-test aggregates may not be present; regenerate the DB and reload.
