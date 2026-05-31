# Phase goal-i_can_see_the_wealthy_future-iter-11 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now **filter the Stock Leaderboard to VCP-flagged names** by selecting "VCP only" (or "Non-VCP") from a new third filter `Select` at the top of `/stocks`, alongside the existing Sector and Setup filters.
- Users can now **see which leading stocks have a detected VCP (Volatility Contraction Pattern)** at a glance — a compact teal "VCP" badge appears in the Setup cell of each flagged row on `/stocks`, sitting next to (never replacing) the setup-status badge.
- Users can now **read why a name is VCP-flagged** by hovering the VCP badge — its tooltip shows the server-built plain-language reason plus the pivot (breakout level) and the invalidation note.
- Users can now **read the full VCP explanation on the Stock Detail page** (`/stocks/[ticker]`): a dedicated "VCP — Volatility Contraction Pattern" card showing the reason, the **Pivot (breakout level)**, the **Invalidation** sentence, and the contraction-depth chips — or an explicit "No VCP pattern detected." line when the stock has no pattern.
- Users can now **judge whether VCP-flagged names actually outperform** by reading a new "Forward return: VCP vs non-VCP" breakdown panel on `/system-health`, which shows each cohort's mean forward return and sample size `n` (with a ⚠ marker when `n` is below the minimum sample).

---

## What Changed in the Visible UI

- **`/stocks` (Stock Leaderboard):** a new "VCP" filter `Select` (All / VCP only / Non-VCP) was added to the filter row; a teal "VCP" badge now appears in the Setup cell of flagged rows; the `n / total` count reflects the VCP-filtered view; and the empty-state message now reads "No VCP-flagged name" / "No non-VCP name" when the VCP filter matches nothing.
- **`/stocks/[ticker]` (Stock Detail):** a VCP badge now appears next to the setup status in the header card when the stock is flagged, and a new dedicated "VCP — Volatility Contraction Pattern" card is shown below (reason + pivot + invalidation + contraction chips, or an explicit not-detected line).
- **`/system-health`:** a new "Forward return: VCP vs non-VCP" breakdown panel now appears in the breakdown grid, alongside the existing "by setup type" and "by market regime" panels.

---

## What Old Behavior Changed

- **Setup status / leaderboard ranking:** unchanged. The VCP flag rides *alongside* setup status and never alters it — a name's setup ("Actionable", "Extended", "Avoid", "Risk-off-watchlist", etc.) and its leadership rank are byte-identical to before this iteration. VCP alone never promotes a name to "Actionable".
- **Stock Detail invalidation block:** unchanged. The existing setup-invalidation line stays as-is; the VCP card adds a *separate* pivot/invalidation specific to the pattern (do not confuse the two — they are distinct levels).
- No other existing behavior changed; all values are re-formatted from the API and nothing is recomputed client-side (the VCP filter is a pure client-side re-display of the server-computed `row.vcp.flagged`).

---

## Not Visible Yet

- The **`/methodology` glossary page and its VCP catalog entry (J-12)** are intentionally deferred to the next iteration. The VCP reason and thresholds are already config-backed so the glossary can render them with no detector change — but there is no `/methodology` page or nav route yet by design. This is **not** a gap in J-16.
- The full VCP `contractions` and `detail` data (volume ratio, distance-from-pivot, contraction count) ride the API per stock; the leaderboard surfaces only the badge + tooltip and the detail page surfaces the contraction chips — the lower-level numeric `detail` fields are not individually rendered.
