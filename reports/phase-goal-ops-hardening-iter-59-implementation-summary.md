# goal-ops-hardening-iter-59 — Implementation Summary

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** developer

---

## Features Implemented

- **The Regime Lab research page can no longer crash the whole app under memory pressure.** Previously,
  if the backend was already busy doing a heavy background computation (like catching up on missed
  historical data) and got close to its memory limit, opening the Regime Lab page (or refreshing it)
  could occasionally trigger an unhandled crash that showed up as a server error. Now, if that heavy
  background computation genuinely runs the server low on memory while someone is loading Regime Lab,
  the page still loads successfully — any individual forward-looking time window ("horizon") that could
  not be computed in that moment is shown honestly as "temporarily unavailable" (with an explanatory
  tooltip) instead of taking the whole page down. Every other time window that did compute successfully
  still shows its real, correct numbers.
- **Restarting the backend is now confirmed safe and fast in practice, not just in theory.** After a real
  data-loading job had run, the backend was stopped and freshly restarted. It came back up in about a
  fifth of a second, and the Data Manager page immediately showed the correct, previously-saved coverage
  numbers (in about six-tenths of a second) — it did not need to re-scan the entire multi-million-row
  price history to do so. The Scanner Runs list and the home page's market-condition card were also
  confirmed to load from storage with zero new database writes triggered by viewing them. Full numbers
  are in the developer handoff and `reports/perf-budgets.md`.

## Changed Behavior

- **The Regime Lab computation now works through one time-window at a time internally, instead of holding
  every time window's raw data in memory simultaneously.** This is an internal efficiency/safety change —
  the numbers shown on the page are provably identical to what they were before (verified by an automated
  test that compares every figure against the old computation method). The only user-visible difference
  is the new, rare "temporarily unavailable" state described above, which only appears when the server is
  genuinely under heavy memory pressure at that exact moment.

## Backend-Only Items

- None — the new "temporarily unavailable" marker, when the backend sends it, is immediately wired up to
  render on the Regime Lab page.

## Corrections Made After Code Review (second pass)

A code reviewer read this work and rejected the first version. Three problems were reported and all three
are now fixed. In plain language:

- **The important one: a rare double-counting bug in the new safety behavior.** The new "isolate the
  failure to one time window" logic recorded each time window's real results into the response as it
  computed them, step by step. If a failure happened *partway through* one time window — after the first
  half of that window's numbers were already recorded, but before the second half finished — the safety
  handler would then add a *second*, "temporarily unavailable" entry for that same time window. The page
  would have received one time window listed twice, with contradictory contents. The reviewer reproduced
  this; so did I, seeing the exact same symptom (time window "1" appearing twice in the list). **Fix:** a
  time window's results are now held aside privately while being computed and are only published into the
  response once that window has fully succeeded — so every time window contributes exactly one entry,
  either its real numbers or the honest "temporarily unavailable" marker, never both. This matches how the
  equivalent, already-proven Factor Lab code has always worked.
- **A test that should have caught it, didn't.** The existing test triggered a failure at exactly the
  vulnerable moment but only checked *which* time windows were marked unavailable, never *how many* entries
  each one produced — so the duplicate slipped past. It now checks that every row lists each time window
  exactly once, in the expected order. Confirmed to have teeth: with the fix deliberately removed, this new
  check is the first thing that fails, with the exact symptom above.
- **A stale comment.** An out-of-date description at the top of the test file still said the old
  "everything at once" approach was in use. Updated to describe what the code actually does now.

**A further problem found while re-checking, and fixed:** the one test left unverified in the first pass
(the one that checks the safety behavior through the real web request path) finally ran to completion this
pass — and it failed. The cause was a flaw in the test itself, not in the product: an earlier test in the
same file had already saved a good copy of that same page's data to the cache, so the new test was served
that saved copy and never actually exercised the safety path it was meant to test. The web request itself
answered correctly (no server error), so the product behavior was fine; the test was simply not measuring
what it claimed to. It now requests a variant that no other test caches, guaranteeing the safety path is
genuinely exercised, and it additionally confirms that a degraded result is never saved to the cache. No
product code was changed for this.

Also worth recording for whoever schedules test runs: that test file takes **just over an hour** of solid
computation on this machine, not the "20 or so minutes" the first pass estimated.

## Incomplete Items

- **The code change itself is complete and its correctness is proven** (an automated test compares every
  number the new, safer computation produces against the old computation and confirms they match exactly).
  The backend-restart verification step is also complete and confirmed clean.
- **One verification gap remains, disclosed honestly rather than glossed over:** a live drill meant to
  exercise the new memory-safety behavior under real, sustained concurrent load was interrupted partway
  through by an environment-level process interruption in the first pass, and was not re-run in this
  correction pass (which was scoped to the reviewer's findings).
  One clean live data point was captured before the interruption (the page loaded correctly under real
  concurrent load, with no crash), and a real availability hiccup was also captured and is disclosed in
  full in `reports/perf-budgets.md` — five brief moments where the health-check endpoint did not answer at
  all during a period of heavy concurrent computation. This hiccup is not caused by this iteration's code
  change (the part of the system responsible was already hardened in an earlier iteration); it is recorded
  as real evidence for a future pass to look at, not hidden.

## Config and Environment Changes

- None. No settings, environment variables, or memory/resource limits were changed this iteration — the
  fix works within the existing, previously owner-approved memory ceiling.

## Known Limitations

- The "temporarily unavailable" marker only appears on the Regime Lab page, and only for the specific
  forward-looking time window(s) that could not be computed at that exact moment — it is not a general
  site-wide error state. If the underlying memory pressure clears (e.g., the background job finishes),
  the very next visit computes and shows real numbers again; a degraded result is never saved and re-shown
  as if it were final.
- This iteration deliberately did not touch the two things the project owner has repeatedly said are
  out of scope for now: moving heavy computations to a separate process, and whether one particular
  internal time budget applies while the site is also serving live visitors. Both remain open,
  owner-level decisions, not something this pass could or should resolve on its own.

---

## Update — verification pass (2026-08-11, after the post-QA audit returned FAIL)

**Nothing about the product changed in this pass.** The audit found the code sound but the *proof* thin:
the two user journeys this iteration exists to close had never actually been run and checked end to end,
and one earlier measurement write-up contained a figure that turned out to be wrong. So this pass ran the
missing checks, on the real running app, and corrected the record. No feature, setting, or line of product
code was altered.

### What was checked, and what it showed

- **"Data is prepared once, when it is loaded — never re-crunched when you open a page."** The full
  journey was driven through a real browser, start to finish: a data-loading job for one previously
  missing historical trading day was started from the Data Manager page, waited out for its real duration
  (**25 minutes 14 seconds**), and then every claim on the screen was checked against what was actually
  saved — the job's own summary panel, the list of which prepared datasets it refreshed, the new date
  appearing in Scanner Runs, and that date's stored snapshot page rendering its real leaderboard.
  **It passed, all 15 checks.**
- **"A big background computation never takes the site down."** The same journey passed its own five
  checks, and — more importantly — the site's health was measured continuously while that 25-minute job
  ran. **1,520 health checks, one per second, every single one answered successfully. None failed, none
  timed out.** In the same window the Regime Lab page was reloaded continuously: **472 loads, all
  successful, no errors of any kind.** Peak memory reached **5,837 MB against the 8,192 MB ceiling —
  71% used, 29% headroom** — measured as the highest point of 1,575 readings rather than a single glance.
- **Restart safety, re-confirmed on this same data.** The backend was killed outright (no graceful
  shutdown) and restarted: **back online in 1.7 seconds**, Data Manager's coverage panel served from
  storage in **0.24 seconds**, and viewing pages created **zero** new database rows. It did not re-read
  the 3.3-million-row price table.
- **The "temporarily unavailable" state was deliberately triggered and looked at, for the first time.**
  Using the built-in test switch, the server was made to fail that computation on purpose while a real
  browser had the Regime Lab page open. The page **stayed up**, showed **"NA" with the tooltip
  "Temporarily unavailable — degraded under memory pressure"** in the affected cells, and invented no
  numbers. The same page with the switch off showed real figures, which is what proves the "NA" came from
  the induced failure rather than from missing data. Screenshots of both were saved and reviewed.
- **The server survived it.** After that induced failure, the *same* server process kept answering health
  checks and kept serving Data Manager, Scanner Runs, market phase and Backtest — byte-for-byte the same
  content as before the failure. No restart was needed, and the failed result was never saved.

### Corrections to the record

- An earlier write-up of the health measurements stated that no health check had been slow. That was
  **wrong**, and it has been corrected in `reports/perf-budgets.md`: the earlier run's slowest answer was
  3.4 seconds, and 15 of 448 checks (not 5) exceeded the target. The corrected figures, and this pass's
  new ones, are now produced by a script that reads the raw logs directly, so the numbers published cannot
  drift from what was measured.
- **This pass's own honest caveat:** while no health check failed, **12 of the 1,520 answered more slowly
  than the 2-second target, the slowest at 4.1 seconds**, during the heaviest part of the background job.
  The site stayed up and truthful throughout; it was briefly slower than the target. Both facts are
  recorded.

### Still outstanding

- **The recorded video-style walkthrough of these two journeys was not produced.** The tool that records
  it runs an interactive, on-screen session that this automated pass cannot drive, and the automated
  retry sequence does not re-run that step. The reason it produced nothing the first time is now fixed —
  the two journeys have real results to narrate — so it should be re-run next iteration.
- **A degraded cell still looks identical to a genuinely empty one** unless you hover over it to read the
  tooltip. Confirmed visually this pass. Fixing it means changing page code, which is deliberately not
  allowed after the verification lane has already run, so it is written up for the next iteration.
- **Whether this change made the Regime Lab's first (uncached) page load slower was not measured**, because
  no equivalent "before" measurement exists to compare against. Recorded as unknown rather than guessed.
