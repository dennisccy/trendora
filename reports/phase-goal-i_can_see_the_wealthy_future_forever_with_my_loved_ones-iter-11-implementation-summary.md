# Iteration 11 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Written by:** developer

---

## Features Implemented

- **Named & described ETFs on the Sectors page (J-58)**: Every ranked row on `/sectors` now shows a plain-language name (e.g. the row that used to read just "KRE" now reads "Regional Banks (SPDR)"), and an industry ETF's expanded panel shows a one-line description of what it is. All names and descriptions come from the config file — nothing is invented in code.
- **Universe-member lists per ETF**: Expanding any ranked row now lists the universe stocks that belong to that sector or industry group. Sector members are the stocks classified into that sector; industry members come from a new config-defined stock→industry-group mapping. The first six members show inline with a "+N" button that reveals the rest (and a "Show fewer" to collapse). Each member ticker is a clickable chip that opens that stock's detail page in a new browser tab, carrying the current as-of date when you are viewing history.
- **Honest empty state**: An ETF with no mapped members (for example "Regional Banks", because the tracked universe contains no regional bank) shows an explicit "No universe members are mapped to this ETF" message instead of any fabricated names.

---

## Changed Behavior

- **Sectors leaderboard rows**: Previously an industry ETF row showed only its bare ticker (e.g. "KRE") and its expanded panel showed only the score component breakdown. Now the row carries a config display name, and the expanded panel additionally shows the description (industry ETFs) and the expandable universe-member list.
- **The scores, ranks, RS-vs-SPY, distance-from-52-week-high, and trend labels are unchanged.** This iteration only adds descriptive information around the existing numbers — no ranked value moved. (Proven by an automated before/after byte-identical test.)

---

## Backend-Only Items

- None. Every backend addition (config name/description, member list) is shown on the `/sectors` page.

---

## Incomplete Items

- None for J-58. All spec items (config catalog, member mapping, validation, persistence, serving, and the frontend panel) are implemented.
- Out of scope by design (separate future iterations): the jobs-pipeline cluster (J-59/J-60/J-66/J-67), the availability heatmap (J-61), the as-of calendar popover (J-62), and event-study episode mode (J-63).

---

## Config and Environment Changes

- `config.yaml` → `etfs.industry`: changed from a plain list of tickers into a catalog mapping each industry-ETF ticker to a required display **name** and an optional one-line **description**. A malformed entry (missing name) now fails loudly at startup rather than silently falling back to the ticker.
- `config.yaml` → new `stock_industries` section: a config-defined, many-to-many mapping of each in-universe stock to one or more industry-group ETF tickers (the same shape as the existing `themes` section). Validated at startup: every stock must be in the universe and every ETF ticker must exist in the `etfs.industry` catalog.
- Database: the stored sector-score table gained two columns — `description` (nullable) and `members_json` (defaults to an empty list). No migration tool is used; the app creates the columns on a fresh database. Existing stored runs that predate the columns render honestly (no description line, empty-state member list) and are never mutated.
- No new environment variables.

---

## Known Limitations

- "Regional Banks (SPDR)" (KRE) genuinely has zero mapped members because the tracked stock universe contains no regional-bank name — this is intentional and demonstrates the honest empty state, not a bug. Banks present in the universe (JPM, GS) are money-center banks and are mapped to the broad "Banks" ETF (KBE) instead.
- The industry membership is config-curated reference data (like themes), not a rule-based screen. It is labelled "config-defined" in the UI so the source is transparent.
- The full backend test suite (~639 tests, 35-45 minutes) cannot complete inside a single automated dev turn. The developer verified the directly-affected modules (config, sectors, themes, indexes, api-engine) and the live persist/serve path end-to-end; the full suite is handed to the pump (see dev handoff for the exact command).
