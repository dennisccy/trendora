# goal-i_can_see_the_wealthy_future_forever-iter-26 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Written by:** developer

---

## Features Implemented

- **Offline test data source for the Data Manager (the "seed" source).** When a single environment switch
  is turned on, the Data Manager's import-source picker gains one extra source called "Seed (offline test
  data)". It serves the project's own committed historical prices — no internet, no API key — so a tester (or
  the automated browser checker) can run a real "pull the missing data" and a real "expand the universe" all
  the way to completion **without any live data provider**. It is OFF by default and is never shown in the
  real product; it exists only so the four already-built Data-Manager features can be demonstrated end-to-end.
- **A reproducible test dataset builder.** A small script builds a throwaway practice database that
  deliberately contains three kinds of "problem" stocks — one with no history, one with too little history,
  and one with a hole in the middle of its history — so the missing-data diagnostic shows all three
  categories, and the offline source can then fill exactly the gaps. The builder never touches the real
  committed data.
- **Clearer feedback when resuming an import that needs a key.** On the Data Manager, if you try to resume a
  paused import that requires a provider key and you have not supplied one, you now see a clear red message
  ("Enter the session key for <source> to resume.") right next to the Resume button, and the import stays in
  the list. Previously this could look like nothing happened.

## Changed Behavior

- **Resume on the Data Manager**: Previously, attempting to resume a key-requiring import without a key could
  appear to do nothing (the row seemed to vanish). Now it shows a visible inline error and the import row
  stays put until you supply the key (or it succeeds).
- **Everything else is unchanged in the real product.** No new pages, no new buttons, no second date control,
  no change to scoring, scanning, snapshots, or any other page.

## Backend-Only Items

- None new that users can't reach. The "seed" offline source and the test-data builder are deliberately
  test/dev-only and are not part of the shipped product.

## Incomplete Items

- **Live-provider versions of these flows remain "not applicable" (by design).** Running an expand or a pull
  against a real, live data provider still depends on a reachable provider (the project's usual provider is
  rate-limited / key-gated for this machine). Per the project's rules, those live outcomes are recorded
  honestly as not-applicable and do not block progress. The offline captures prove the features work.
- **The browser captures themselves are QA's job.** This iteration delivered the enabler (the offline source
  + the test dataset) and the small Resume fix; the actual recorded walkthroughs are produced by the QA/
  browser steps.

## Config and Environment Changes

- `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` — turns the offline "seed" import source on. Default: unset (OFF).
  Only used by the test/QA harness; never set in production.
- `TRENDORA_SEED_IMPORT_DIR` — points the offline "seed" source at a throwaway folder (used so an offline
  "expand the universe" writes its results there instead of the real committed data). Default: unset (uses
  the committed data, read-only). Only used by the test/QA harness.
- No database migration. No change to `config.yaml`. The offline source is intentionally NOT added to the
  committed provider catalog.

## Known Limitations

- The offline "seed" source is for testing and demonstration only. It must stay off in production; it is off
  by default and is absent from the committed configuration, so this is safe.
- An early experiment (before a safeguard was added) briefly overwrote a few committed price files because an
  offline "expand" wrote results into the real data folder. This was caught, the data was restored exactly,
  a safeguard now routes those writes to a throwaway folder, and an automated test guards against it
  recurring. The committed data is verified clean.
- A market-cap figure for the offline source comes from a small committed reference list; a stock not on that
  list is honestly reported as "no market cap" rather than being given a made-up value.
