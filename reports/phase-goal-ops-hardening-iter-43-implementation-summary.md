# goal-ops-hardening-iter-43 — Implementation Summary

**Phase:** goal-ops-hardening-iter-43
**Date:** 2026-07-31
**Written by:** developer

---

## Features Implemented

- **Undo of last iteration's memory tweak**: the change made last iteration to how the app loads price
  history into memory (a filter meant to save some memory) turned out to make memory usage slightly
  *worse* once you account for its knock-on effects, not better. This iteration undoes just that
  filter and goes back to the simpler, proven approach.
- **Honest failure when a data job can't even start**: if the server is under enough load that it
  literally cannot start a new background worker thread (a rare but real failure mode), the job now
  correctly shows up as "failed" with an explanation instead of silently sitting at "running" forever
  with no further updates. The person who requested it also now gets a clear error message right away
  instead of a misleading "started successfully" response.
- **Frontend launch script now respects the same hardware safety limits as the backend**: the script
  that starts the web frontend didn't previously apply this machine's CPU/thread safety caps (the ones
  put in place after this machine's hardware reset incidents). It now does, matching the backend
  launcher.

## Changed Behavior

- **How the app loads a full symbol's price history internally**: previously (as of last iteration),
  when loading price data in bulk, the app would skip loading a handful of index/sector ETF symbols up
  front and instead load them one at a time on demand. That "optimization" is now removed — it now
  loads everything up front again, the way it did before last iteration, because the on-demand path
  turned out to cost more memory overall, not less.
- **Data job error responses**: starting a backfill or resume job that fails to launch (an internal
  server-capacity issue, not a user input error) now returns an honest "service unavailable" response
  instead of a false "it's running" response.

## Backend-Only Items

- The job-launch-failure fix is a pure backend/API behavior change — there is no new UI element, because
  the existing "job failed" display already covers this case once the backend reports it correctly.

## Incomplete Items

- **This iteration's headline gap: the live "does the memory fix actually hold up under a real, full
  workload" test did not finish.** We triggered a real historical-data backfill against the full
  production-sized database to re-verify that a heavy background computation (re-analyzing all
  historical trading data) stays within the newly-raised memory limit and keeps the app responsive
  throughout. We watched it closely for about 17 minutes of continuous observation (~28 minutes total
  including setup):
  - **The memory question is answered, cleanly, and it's good news**: memory usage stayed completely
    flat the entire time, comfortably within the new limit (using about a third of what's allowed).
    This was the main thing this iteration needed to confirm, and it held up.
  - **The app never went down or stopped responding** — every single health check during the test
    succeeded.
  - **However, the app did get noticeably slower to respond during this heavy computation** — response
    times crept up over the course of the test (from roughly 1.7 seconds up to over 3 seconds on
    average, some spikes past 6 seconds) rather than staying fast. This is a real, newly-observed
    slowdown, not something this iteration caused outright — it's most likely an amplified version of
    a known, already-documented speed issue from two iterations ago (which was explicitly left for a
    future iteration to address), now more exposed because of this iteration's memory fix. It was not
    fixed this iteration; it is flagged clearly for the next one to investigate.
  - Because the background computation never finished within the observation window, we could not get
    the very last piece of confirmation we wanted — that once such a computation finishes, its results
    are correctly saved and show up as "already computed" the next time someone looks. We had to stop
    the test partway through. When we restarted the app afterward, everything recovered cleanly and
    correctly (the app came back up in about a second, the partially-run job correctly showed as
    "interrupted" rather than stuck, and no data was lost or corrupted) — so the recovery behavior is
    confirmed even though the original computation's own completion was not.
- A full click-through re-test of the six other user journeys that are supposed to still be working
  (backfill honoring date ranges, no artificial range limits, non-blocking startup, per-page minimal
  loading, backtest evidence, and the app disclosing its own background activity) is expected to happen
  in the browser-testing step that follows this one, not in this implementation pass. Some of those were
  spot-checked directly against the running server this session and looked correct, but that is not a
  substitute for the full browser-driven check.

## Config and Environment Changes

- No new environment variables or config file settings were added. The memory limit itself
  (`memory_cap_mb: 8192`) was already raised by the owner before this iteration started — this
  iteration did not touch that number, only re-verified behavior against it.

## Known Limitations

- The response-time slowdown described above under "Incomplete Items" is real and unresolved. It does
  not put the app at risk of crashing or running out of memory (that part is fine), but a heavy
  background computation may now make the app feel sluggish for longer than expected while it runs.
- A previously-known, already-documented internal performance quirk (from two iterations ago, tracked
  separately) likely explains most of the slowdown above, but this was not proven or fixed this
  iteration — it remains an open item for a future iteration to look into.
- The internal price-loading mechanism this iteration reverted to is efficient in terms of memory
  *shape* (it uses a compact storage format) but still loads a symbol's entire price history at once
  rather than only the portion needed — this has been true since before this iteration and is a known,
  accepted limitation, not something this iteration changed for better or worse.
