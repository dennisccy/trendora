# Goal iter-33 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Date:** 2026-06-18
**Written by:** developer

---

## Features Implemented

- **Point-in-time stock universe**: The list of stocks the scanner scores is no longer a fixed list of
  122 names. It is now recomputed for whatever date you are viewing — a name only counts as a member once
  it has enough price history, a high-enough share price, and enough trading liquidity, all measured from
  data on or before that date. Early dates honestly show a smaller (or empty) universe that grows over time.
- **"Universe (as of date)" coverage figure**: On Data Manager, the universe count now reflects the date
  you are viewing (it changes as you step the global date switcher). A separate "Candidate universe" figure
  shows the full screened candidate list it is drawn from.
- **Per-date universe diagnostic (Data Manager)**: A new panel explains exactly why the universe is the
  size it is at the current date — how many names were admitted and how many were excluded for each reason
  (not enough history / price too low / liquidity too low) — plus the exact cutoffs used.
- **Membership timeline (Data Manager)**: A new panel charts how the universe size grew over the snapshot
  dates (a step line), lists which names entered and exited on which date, and shows the excluded counts per
  date. It carries three plain-English honesty labels (the survivorship caveat, the warm-up note, and the
  universe-relative note) word-for-word from the backend.
- **"Extend history backward" control (Data Manager)**: A confirm-gated button that attempts to fetch
  earlier price history (best-effort) so the universe can resolve further into the past. When the data
  provider is unreachable, it shows an honest "blocked / limited-coverage (NA)" outcome and never invents
  data, and never halts the system.
- **Honest empty-universe state on the Stock Leaderboard**: At an early/warm-up date the leaderboard shows
  a clear "no ranked stocks at this date — warm-up" message instead of an error or fabricated rows.

---

## Changed Behavior

- **Stock Leaderboard / Themes / Sectors / Scanner Runs**: Previously every view showed the full static
  universe at every date. Now they show only the names that qualify at the date you are viewing — so early
  dates show fewer (or zero) stocks, and the membership grows toward full around early 2022.
- **Latest-date universe size**: Previously 122 names. Now 120 at the latest date — two names (RPD, DNN)
  honestly fall below the minimum share price and are excluded. This is the intended point-in-time behavior.
- **Data Manager "Universe" figure**: Previously a single fixed number. Now date-dependent (members
  resolved at the viewed date), shown alongside the static candidate count and the full candidate-pool size.
- **Methodology → Universe Selection**: Now describes two layers — the candidate-pool screen (which still
  uses market cap) and the per-date membership rule (history + price + liquidity, market cap dropped per
  date because it has no historical series). No displayed number is hard-coded.

---

## Backend-Only Items

- None. Every backend addition (the per-date diagnostic, the membership timeline, the survivorship label,
  the as-of-dependent universe count) is surfaced on the Data Manager UI.

---

## Incomplete Items

- **J-95 real backward-history fetch** — the confirm-gated control, the survivorship label, the
  seed-never-deleted clear, and the resolver resolving earlier dates once bars exist are all done. The
  ACTUAL fetch of earlier real price history is blocked by the data provider on this host, so that leg is
  recorded honestly as blocked / limited-coverage (NA) — by design, non-halting, never faked.
- **J-95 true point-in-time index-constituent feed** — offered only as a data-dependent enhancement; absent
  here, so the candidate pool stays the documented current-constituent listing with its honest label.

---

## Config and Environment Changes

- None. No new config keys, no schema/migration change, no new environment variables. The resolver sources
  all its cutoffs from existing config (`universe.filters.*`, `indicators.min_history_bars`); the new
  diagnostics are read-only derivations over existing stored bars and snapshots.

---

## Known Limitations

- **Warm-up / bootstrap is slower on the full real seed** (~2 minutes when bringing the test database to
  full history): the universe is now recomputed per date. This was optimized (one grouped query skips the
  un-fetched pool names; the timeline caches bars once), and the live app does this work in the background,
  so normal page loads are unaffected.
- **The universe is genuinely empty before ~October 2021** on the committed data (no name has 200 trading
  days of history yet) and fills toward full around early 2022. This is honest warm-up behavior, not a bug.
- The membership-timeline chart is a compact step-line (no axis labels) sitting below the fold on Data
  Manager — deliberately dense to match the existing coverage panels.
