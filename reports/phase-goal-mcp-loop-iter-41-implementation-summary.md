# goal-mcp-loop-iter-41 — Implementation Summary

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

- **Drawdown & dry-spell expectations panel on the Evidence page**: opening any certified claim's card on
  `/evidence` now shows, per market phase the stock was in when the position was entered (Expansion,
  Pullback, Correction, Bear, Recovery), what that cohort's strategy has historically felt like to hold —
  a typical (median) and worst-case (90th-percentile) drawdown depth, how many days it typically spent
  underwater before recovering, how long recovery typically took, and the longest streak of losing
  periods in a row. Every figure carries an honest sample count, and any phase with too few historical
  examples reads "insufficient" instead of guessing. This applies to all 7 currently-certified claims,
  regardless of whether the claim itself passed or failed its statistical test — it is a purely
  descriptive history lesson, never a promise about the future.
- **A full rebuild of the underlying price-history database** was run twice, end to end, to populate the
  two new pieces of data (days-underwater and days-to-recover) across the entire ~30-year, 590-symbol
  history. This was measured to stay well within the platform's memory safety limit on both runs.

## Changed Behavior

- **The Evidence page (`/evidence`) now takes noticeably longer the very first time it is opened after any
  database rebuild** (about 9-10 seconds instead of instant) while the new panel's figures are computed
  for every claim. Every subsequent visit — by anyone, until the next rebuild — is instant again (under
  20 milliseconds), because the result is now cached the same way every other analysis page in this
  product already caches its numbers. This one-time cost was discovered and fixed during this build; it
  is documented in `reports/perf-budgets.md`.
- No existing score, ranking, or evidence verdict changed. The three main scores (Leadership, Entry
  Quality, Risk), the certified-claims ledger's verdicts, and every other page are unaffected — this is a
  purely additive feature.

## Backend-Only Items

None — the new capability has full UI wiring on `/evidence`.

## Incomplete Items

None from this iteration's spec. One follow-up recommendation: an actual visual, in-browser confirmation
of the new panel (scrolled into view, since it sits below the fold on each claim card) is recommended as
the next QA step — this build verified the underlying data and page code thoroughly, including live checks
against the real database, but did not drive an actual browser session.

## Config and Environment Changes

- `config.yaml`: two new required settings under the existing `walk_forward:` section —
  `underwater_horizons` (which holding-period lengths the new panel covers; set to cover every length the
  product already supports) and `streak_min_n` (the minimum number of historical periods needed before the
  "longest losing streak" figure is shown, rather than "insufficient").
- No new environment variables.
- No formal migration tool is used in this project; the two new database columns are added automatically,
  in place, the next time the app starts against an older database file (no data loss, existing rows read
  as "unknown" until the next full rebuild repopulates them — this is the same pattern used for every
  previous addition of this kind).

## Known Limitations

- The very first person to open `/evidence` after any future full database rebuild will experience the
  ~9-10 second one-time load described above (a rebuild is an infrequent, deliberate operator action, not
  something that happens during normal use).
- The new panel was verified with real data through the backend API and by careful code review, but not
  yet through an actual browser click-through; that visual pass is recommended before this is considered
  fully signed off end-to-end.
