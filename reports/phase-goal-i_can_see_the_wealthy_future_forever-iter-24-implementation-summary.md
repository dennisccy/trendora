# Iteration 24 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Written by:** developer

---

## Features Implemented

- **Per-symbol coverage table (J-36)**: The Data Manager page now shows, for every ticker the app holds
  data for and every member of the scored universe, a row stating whether it is in the universe, whether it
  has any price data, its date range, how many bars it has, and a "thin" or "missing" flag. A symbol with
  no data is honestly shown as missing with no date range — nothing is faked.
- **Plain-language coverage definitions (J-36)**: Every coverage figure (price history, universe, symbols,
  trading days, snapshot dates, backfill gaps) is shown next to a one-line explanation, plus a clear
  "universe vs symbols" sentence (the universe is the scored, screened names; symbols is every ticker with
  bars, which also includes the market/sector ETFs and the volatility index).
- **Filter and sort the coverage table (J-36)**: The operator can type to filter by symbol, sort by symbol
  or bar count, and toggle "Universe members only" to confirm every scored name either has data or is
  flagged missing/thin.
- **Seed-safe Remove imported data (J-39)**: A new control lets the operator delete data they imported
  beyond the shipped seed, by symbol and/or date range. Before anything is deleted, a confirm-preview shows
  exactly what will go: how many user-added bars (and over what date range), which committed-seed bars are
  protected and kept, and which derived snapshots and forward-return rows will be removed alongside. The
  operator must explicitly confirm. The shipped seed can never be deleted, and a removal that would only
  touch the seed is refused with a clear reason.

---

## Changed Behavior

- **Data Manager `/api/data` response**: The `coverage` block now additionally carries a `per_symbol` list
  (the table above). Existing fields are unchanged. Pages that only read the old fields are unaffected.

---

## Backend-Only Items

- None. Both new API endpoints (`POST /api/data/remove/preview`, `POST /api/data/remove`) are wired to the
  `/data` UI.

---

## Incomplete Items

- **J-35 browser capture**: The Expand-universe machinery and its result display are built and proven by
  integration tests; the end-to-end browser recording (run an injected-provider expand → see passers +
  omitted-with-reason → grown universe count) is performed by the QA/browser step, not the developer. No
  code was missing for it.
- **J-37 / J-38**: Deliberately out of scope this iteration (deferred to the next). Not started.

---

## Config and Environment Changes

- None. No new environment variables, no new config keys, no database migration, no new tables. The "thin"
  threshold reuses the existing `indicators.min_history_bars` config value; the seed boundary reads the
  already-committed `apps/backend/data/seed/meta.json`.

---

## Known Limitations

- The destructive removal was not run against the live host because it holds real user-imported bars and
  the local database is not version-controlled (no restore). Its correctness is proven by automated tests
  that add user data beyond the seed and verify the exact cascade; on the live host only the read-only
  preview was exercised.
- Coverage and removal are descriptive/curation operations only — they never recompute or change any score,
  return, bucket, or setup. Removal only deletes; it fabricates nothing.
- This iteration does not complete the overall goal — additional Data-Manager journeys (missing-data
  diagnostic, unified unfinished-imports actions) remain for a later iteration.
