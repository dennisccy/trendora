# Goal Iteration 36 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36
**Date:** 2026-06-19
**Written by:** developer

---

## What this iteration fixes (plain language)

The Data Manager page at `/data` had stopped loading. After the large data rebuild in iteration 35,
the page's coverage view tried to recompute a "membership timeline" (how the tradable universe grew
date by date) from scratch on every single page load. With ~1369 dates of history now stored, that
recomputation took longer than five minutes, so the page just showed loading skeletons forever.

This iteration makes the page load quickly again **without changing a single number it shows**. It
does this by computing the timeline once, saving the result, and serving the saved result on later
requests — the same trick already used for the Research event-study and the Market-Phase panels. The
saved result is automatically thrown away and recomputed whenever the underlying data changes, so it
can never show stale figures.

---

## Features Implemented

- **Membership-timeline result cache**: The expensive J-96 membership-timeline computation
  (per-snapshot-date universe size, entries, exits, and per-date excluded-by-reason counts) is now
  computed once and stored in a new internal cache table, then served from storage on subsequent
  `GET /api/data` requests. The served values are byte-for-byte identical to the old slow computation.
- **Automatic cache refresh on any data change**: The cache is keyed by the same single-sourced
  dataset-version stamp the Research and Market-Phase caches already use, so it refreshes by itself
  after any backfill, removal, or rebuild — a stale entry is never served (and is pruned on write).
- **Warm-up precompute**: The background warm-up process (the same one that builds the historical
  snapshots after boot) now also precomputes this timeline cache off the boot path, so the first
  `/data` request after a restart or rebuild is served from the cache rather than paying the slow
  computation in the request.

---

## Changed Behavior

- **`GET /api/data` (the `/data` Data Manager page)**: Previously recomputed the membership timeline
  on every request, which hung for >5 minutes on the post-rebuild dataset (the page never hydrated).
  Now it serves the timeline from a result cache and returns within a normal page load. Every value
  in the served coverage block — `membership_timeline`, `universe_diagnostic`, `universe_count`, and
  all others — is unchanged.
- **Background warm-up**: Now additionally precomputes the membership-timeline cache after building the
  forward returns. A failure of this single step is caught and logged and does **not** fail the
  warm-up (the rest of the warm-up already succeeded).

---

## Backend-Only Items

- None. This is a pure backend read-path performance fix. There is no new endpoint, no new displayed
  value, and no new UI surface. The `/data` page components are unchanged — they simply hydrate again
  once the endpoint responds quickly.

---

## Incomplete Items

- None. All in-scope spec items are implemented: the cache table, the cache read/upsert wrapper, the
  warm-up precompute, the `test_db.py` registration, and the byte-identity / invalidation / causality /
  empty-DB / warm-up unit tests.
- Out of scope (unchanged, per the spec): J-22 / J-23 / J-24 remain honestly data-walled.

---

## Config and Environment Changes

- **No new config field.** Following the existing event-study and market-phase cache precedent, the
  cache is keyed only by the dataset-version stamp with no staleness/batch tunable, so no
  `config.py` field was needed (the plan flagged this as the likely outcome).
- **New internal table `membership_timeline_cache`** is created automatically on boot by the existing
  additive `create_all` step. No manual migration is required: an existing live database gains the
  table on the next restart, and no existing table is altered. (No Alembic in this project.)
- No environment variables added or changed.

---

## Known Limitations

- The very first `GET /api/data` after a cold restart, if it arrives **before** the background warm-up
  has finished precomputing the timeline cache, will compute the timeline once (a cache miss) and then
  serve every later request from the cache. On the live 1369-date dataset this cold compute was measured
  at **97 seconds** (down from ~240 seconds before this iteration's cold-miss optimization), and it does
  not change any served value. In normal operation the warm-up precompute means the first request after
  boot is already a cache hit (served near-instantly), so the 97-second path is only ever hit in the
  brief window before warm-up completes.
- The cache table grows by at most one row per distinct dataset version; older-version rows are pruned
  on every write, so it does not grow unbounded as the dataset matures.
