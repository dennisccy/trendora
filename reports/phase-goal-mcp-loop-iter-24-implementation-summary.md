# goal-mcp-loop-iter-24 — Implementation Summary

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** developer

---

## Features Implemented

- **Storage-footprint card on the Data Manager page**: the `/data` page now shows a small card with the
  database's current disk size and how many price bars, scored results, and forward-return records it
  holds. Numbers are real, read live from the database — never estimated or cached stale.
- **Faster core pages and API responses**: the stock detail page, the health/status check, and the
  Data Manager's dataset-overview panel all now respond noticeably faster, especially on the platform's
  deep (30-year) historical dataset. No numbers on any page changed — only how quickly they arrive.
- **Measurement tooling**: a new operator script (`scripts/measure-perf.sh`) that times the platform's
  key pages and API calls against a running instance and records the results, so future changes can be
  checked against a committed baseline instead of guesswork.

## Changed Behavior

- **Stock detail page and watchlist**: previously, opening one stock's detail page or viewing the
  watchlist required the server to read and parse every stock's stored result before picking out the
  one(s) needed. It now reads only the requested stock(s) directly. The displayed values are identical —
  this is purely an internal efficiency change.
- **Health/status check**: previously, the small "is the system ready" indicator re-did a moderately
  expensive calculation on every automatic refresh (about every 2 seconds). It now reuses that
  calculation until the underlying data actually changes, making the indicator itself faster to update.
- **Database file behavior**: the database now uses a different internal write mode ("WAL") that lets
  the app keep reading smoothly while background jobs write in the background, instead of readers
  occasionally waiting on writers. This is an internal engine setting; it does not change any data or
  displayed value. One side effect: the database folder will now contain two small companion files
  (`-shm`, `-wal`) alongside the main database file when the app is running — this is expected and
  normal for this write mode, and (like the main database file) these companion files are excluded from
  version control.
- **Database structure**: two duplicate/redundant internal lookup structures ("indexes") were removed
  from the database, and one new one was added to speed up date-range lookups. This changes only how
  fast the database answers certain questions — it never changes what the answers are. This was verified
  directly against the real committed database (not just a test copy): the change applies in about 1.3
  seconds, even against a database with over 3 million stored price rows.

## Backend-Only Items

None — every backend change in this iteration is either invisible-by-design (an internal performance
optimization with no new user-facing surface) or has a corresponding UI element (the storage-footprint
card).

## Incomplete Items

None from this iteration's scope. Everything specified for items B, C, D, G, H, and K (backend +
measurement harness + storage card) was implemented, tested, and verified live against running services.

Two related but explicitly out-of-scope items remain for future iterations (per this iteration's plan,
not a gap): shrinking the main stock-list response payload, and speeding up the background data-import
jobs by roughly a third. Both are called out in the project's roadmap as their own future iterations.

## Config and Environment Changes

- `config.yaml` → `database.pragmas` (new block): the internal database tuning settings described above
  (write mode, timeout, cache size). Sensible defaults are built in — no action needed to pick these up.
- `config.yaml` → `database.pool_size` / `database.max_overflow` (new keys, defaults `10`/`20`): how many
  simultaneous database connections the app keeps ready. No action needed.
- No new environment variables. No database migration script is needed — the database structure changes
  (index cleanup) apply themselves automatically and safely the next time the app starts, whether on a
  brand-new database or the existing one.

## Known Limitations

- The new measurement script's "one bounded backfill timing" check picks a date range from the
  platform's own gap list to time a real backfill job. On a database that is already fully caught up
  (as it was during this iteration's live verification), that range can legitimately contain no
  actionable dates, so the timing reflects a fast "nothing to do" result rather than real backfill work.
  This is expected and honestly labeled in the recorded output — it is not a malfunction, but it means
  that particular number isn't the most illustrative example of backfill speed. A future iteration could
  make the script smarter about picking a genuinely actionable date range.
- This iteration's automated test suite took unusually long to run on this particular machine (multiple
  hours total, driven by the one-time cost of building a 30-year test dataset) — this is a pre-existing
  characteristic of testing against the platform's full historical depth on this hardware, confirmed to
  be unrelated to this iteration's changes (every individual piece of the slow path was separately timed
  at well under 10 seconds against the real, live database). It does not affect how fast the actual
  running product is for a real user — only how long the test suite takes to prepare its test data.
