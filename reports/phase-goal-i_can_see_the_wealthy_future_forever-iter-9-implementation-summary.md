# Goal Iteration 9 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Two new detected price patterns beyond VCP**: Trendora now detects three price patterns instead of one. The two additions are:
  - **Pullback to a rising DMA** — an uptrending stock that has pulled back *to* its rising moving average (rather than crashing), a lower-risk continuation entry.
  - **Flat-base breakout** — a shallow, sideways base built at the highs with price coiled just under the pivot on building volume, breakout-ready.
- **Filter the leaderboard by each pattern**: On the Stocks page the old "VCP" filter is now a single "Pattern" dropdown that can show only the names flagged for any one of the three patterns (or hide them). Filtering shows only the matching rows, or an honest "no stocks match" message — never fabricated rows.
- **Inline pattern badges + explanations**: Each flagged stock shows a small teal badge per pattern (e.g. "Pullback", "Flat base") on both the leaderboard and the stock detail page. Hovering the badge shows the plain-language reason, the pivot price, and the concrete invalidation level — all written by the backend and shown verbatim. A second hover-tooltip gives the pattern's glossary definition.
- **Two new glossary cards**: The Methodology page now documents both new patterns automatically — their meaning, the exact config thresholds that define them (read live from the config so they always match the scanner), and a worked example.
- **Two new forward-tested evidence panels**: The System Health page now shows, for each new pattern, the average realized forward return of the flagged names vs the non-flagged names, each with its sample size — so a user can judge whether the pattern actually adds value. Cohorts below the minimum sample size show "NA" with the count, never a made-up number.

---

## Changed Behavior

- **Stocks leaderboard filter**: Previously there was a "VCP" filter with three choices (All / VCP only / Non-VCP). Now there is a "Pattern" filter that covers all three patterns (each with an "only" and a "not" option). Filtering by VCP works exactly as before.
- **Stock detail page**: Previously showed only the VCP badge + VCP card. Now also shows a badge and a detail card for each of the two new patterns when a stock is flagged for them (the VCP card is unchanged and still always present).
- **Methodology page**: The page subtitle now says "detected price pattern" (plural) instead of naming VCP specifically. The new pattern cards appear automatically from the config catalog — no other change.
- **Stored daily snapshots**: Each saved scan result now also records whether the stock flagged each new pattern (two new yes/no columns), mirroring the existing VCP flag. The three independent scores, the A–E buckets, the setup status, and the market regime are completely unchanged — the new patterns only ride alongside them.

---

## Backend-Only Items

- None. Every new backend capability is surfaced in the UI (leaderboard filter + badges, glossary cards, System Health breakdowns).

---

## Incomplete Items

- None of this iteration's scope was deferred. The two target patterns are fully implemented end-to-end (detection → storage → forward-test → API → UI → tests).
- **Out of scope by design (not built this iteration):** the `/research` labs (J-25–J-31), the data-walled universe-expansion journeys (J-22/23/24), and any third+ pattern. The `/research` nav entry was front-loaded into the blueprint by the decomposer for a future iteration — no `/research` code exists in this diff.

---

## Config and Environment Changes

- `config.yaml` → `patterns.pullback_to_rising_dma` — all detection thresholds for the pullback pattern (MA basis, rising-trend lookback + minimum slope, proximity-to-MA band, maximum pullback depth, minimum history, volume window). No environment variable; tuned against the committed offline seed.
- `config.yaml` → `patterns.flat_base_breakout` — all detection thresholds for the flat-base pattern (lookback window, base window, maximum base depth, pivot proximity, minimum history, volume window + minimum breakout-volume ratio).
- `config.yaml` → `methodology.entries` — one `kind: pattern` glossary entry per new pattern, with the numbers referenced live from the config keys above (never re-typed).
- **No environment variables changed.** No secrets, no keys, no network. The patterns are computed purely from the committed offline price seed.
- **Database is regenerated, not migrated.** `apps/backend/data/trendora.db` is rebuilt on boot from the frozen seed; it was deleted and recreated so every immutable snapshot carries the two new pattern flags. This is offline and deterministic — no live fetch.

---

## Known Limitations

- **Honest small samples in the forward-test.** With the quarterly walk-forward cadence, a pattern that flags few names can produce a small cohort. Those cohorts correctly show "NA" with the sample count rather than a fabricated return. (At the default 20-day horizon both new patterns currently clear the minimum-sample threshold; the VCP cohort can sit below it — that is shown honestly, not hidden.)
- **Patterns are descriptive, not predictive.** A flagged pattern never changes a stock's setup status and never by itself makes a name "Actionable"; Risk-Off still forces zero Actionable names. The forward-test evidence carries the same survivorship-bias caveat as the rest of System Health.
- **The pivot label on the detail card is generic** ("Pivot (breakout level)") and is reused across patterns; for the pullback pattern it is the recent high (the level whose reclaim resumes the trend), for the flat base it is the base high.
