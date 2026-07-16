# Phase goal-mcp-loop-iter-41 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the Evidence page (`/evidence`), users can now read a new **"Historical drawdown & dry-spell expectations" panel** on every certified claim card, showing what following that claim's cohort has historically felt like to hold, broken out by the market phase the position was entered in (Expansion, Pullback, Correction, Bear, Recovery — always shown in that order).
- For each phase, users see four historical measures side by side — typical (median) and worst-case (90th-percentile) **max-drawdown depth**, typical **days spent underwater**, typical **time to recover**, and the **longest streak of consecutive losing periods** — each carrying its own honest sample size (`n`).
- Users can read, in plain language directly below the table, exactly how the "longest losing streak" number is counted (once per walk-forward date, so multiple stocks sharing the same date are never double-counted as separate losses) and a survivorship-bias caveat reminding them the figures likely run optimistic and should be read as an upper bound, not a guarantee.
- This panel renders on all 7 currently certified claims, including all 7 that currently show a FAIL verdict — it is descriptive cohort history, not gated on whether the claim itself passed its own statistical test.
- Where a phase has too few historical examples to trust (today, for example, the "Breakout-watch" event-study claim's Correction and Bear rows have zero matching observations), users see the honest label **"insufficient (n=…)"** in place of a guessed number — this is already happening on today's live data, not just a theoretical edge case.

## What Changed in the Visible UI

- Every claim card on `/evidence` now has a new section appended below the existing "Hypothesis / Out-of-sample verdict / Control comparison / Registration date / Forward-walk score-to-date" field grid: a heading reading "Historical drawdown & dry-spell expectations ({N}-day hold)", a one-line disclaimer that this is history and not a forecast, and a 5-row table (one row per market phase, four measure columns).
- Below that table, every card now shows a fixed method-note sentence and a fixed survivorship-bias sentence, worded identically across all 7 cards (read verbatim from the API response, never authored per-claim in the browser).
- The five phase names in the new table are shown as badges — but unlike every other phase badge already in the product (e.g., the phase badge on the main dashboard, which is color-coded by severity), these new badges are all the same flat neutral gray for every phase. This is a MINOR cosmetic inconsistency flagged in code review, not a data problem — the underlying figures are unaffected.
- No new page, no new route, and no navigation change — the panel is purely additive content inside the pre-existing `/evidence` claim cards; the page's heading, loading skeleton, empty state, and error state are all unchanged.

## What Old Behavior Changed

- `/evidence` now has a one-time-per-database-rebuild slow path: the very first request for the page's data after any full database rebuild takes about 9-10 seconds (all 7 claims' new figures are computed together in that single request), whereas previously this page always loaded near-instantly. Every visit after that first one — by anyone, until the next rebuild — is fast again (a few milliseconds), because the result is now cached the same way other analysis pages in the product already cache their numbers. This was discovered as a ~3x latency regression during this build and fixed (via caching) before shipping — see `reports/perf-budgets.md` Item I.
- No existing score, verdict, badge, or field on `/evidence` changed. The "Out-of-sample verdict" badges (still 7/7 FAIL today), the Hypothesis/Control-comparison/Registration-date fields, the regime badge, and every other page in the product are unaffected — the new panel is strictly appended below the pre-existing content, never interleaved with it.

## Not Visible Yet

- None. Every backend capability built this iteration (the two new stored per-observation columns, the phase-conditional aggregation, and the cache that keeps it fast) is reachable today through the new `/evidence` panel — there is no backend-only piece left unwired. (The underlying config gate, `walk_forward.underwater_horizons`, currently covers every horizon the product serves, so no certified claim is silently excluded from the panel today.)
