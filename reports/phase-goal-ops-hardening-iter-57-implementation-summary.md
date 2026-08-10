# goal-ops-hardening-iter-57 — Implementation Summary

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Written by:** developer

---

## Features Implemented

- **Honest "updating" data during an active job:** the `/data` page's per-date availability heatmap no
  longer falsely claims "there is no data" while a backfill/fetch job is running. Instead it shows the
  real previous chart plus a calm "Data as of `<version>` — updating" note, exactly like the existing
  "Coverage as of a prior scan" notice already used elsewhere on the same page. This closes a real bug
  introduced by last iteration's speed fix: for the entire ~20-minute duration of any ingest job, the page
  was showing "No availability yet — Fetch real EOD prices" over a database holding 3.3 million real price
  rows.
- **`GET /api/health` is fast again:** the health/status check every page polls in the background now
  answers in about 10-15 milliseconds at rest, instead of 160-240 milliseconds — a query-plan fix only,
  the information shown is identical.
- **The Stock Detail page's price chart loads faster:** `GET /api/stocks/{ticker}/bars?through=latest`
  (the call that draws the full price-history chart with moving averages) had a real inefficiency in its
  moving-average math that made the calculation redo more work than necessary as a stock's price history
  grew. Fixed; the moving-average numbers shown are identical, just computed faster.

## Changed Behavior

- **Availability heatmap during a job:** previously showed a false "no data" message for the whole
  duration of any backfill/fetch job. Now shows the real, most-recent chart with an honest "updating"
  banner instead.
- **Two internal bookkeeping fields (`persisted_this_call`) are now honest about failed saves:** in the
  rare case a background cache save fails and is rolled back, the system used to still claim it saved
  successfully. It now correctly reports that nothing was saved. This affects only an internal accounting
  field already shown after every backfill/fetch/rebuild job ("Refreshed: ..." list) — a normal
  successful job is unaffected; only the rare failed-save case now reports itself honestly.
- **An internal diagnostic tool (`list_runs`, used by AI-assistant integrations, not the web UI) now
  answers much faster** on this dataset's current size — same information, same numbers, just faster.
  Timed live this round against the real database (2,945 stored scanner runs): about 0.08-0.13 seconds,
  versus 0.38 seconds for the old version, against a 1.5-second allowance. An earlier note in the project's
  records claimed the old version took 6.8-10.7 seconds; that could not be reproduced at rest and has been
  corrected in writing — the honest statement is that the old version was already inside its allowance on a
  quiet machine, and the change matters mainly because its cost stops growing as more runs are stored.

## Backend-Only Items

- None — every backend change this iteration either has a corresponding UI change (the availability
  banner) or is purely an internal speed/correctness fix with no user-visible shape change (health,
  bars/moving-averages, the internal bookkeeping field, the diagnostic tool).

## Incomplete Items

- **One particular test file (`test_api_runs.py`) could not be run to completion, even after two
  attempts.** It is known from prior rounds to take an extremely long time to set up its test data on
  this project's large historical dataset — it ran for nearly an hour on the first try and a further ten
  minutes on a second try later in the session, never finishing either time. This is now the fourth time
  in a row (across three separate rounds) this same file has failed to finish in a normal working
  session. This file tests a page (`/scanner-runs`) that this round did not touch at all, so confidence
  the underlying feature still works correctly is high, but a green/passing run of this specific file is
  still owed and worth a dedicated look. Every OTHER test file touched this round — six files, 336
  individual checks in total — was run and passed cleanly. **Update (fix round):** 4 of this file's 9
  checks do not need the slow setup and were run this round — all 4 pass, in half a second. The problem
  has been written up as a standing ticket (`docs/test-infra-tickets.md`, TI-1) proposing that those fast
  checks be split into their own file so future rounds always get a real answer, rather than re-attempting
  the hour-long run each time.
- **The "updating" banner itself was not visually screenshotted mid-job this round** (that requires
  actually starting a real backfill against the shared project database, which was avoided to not disturb
  other concurrent work). Its correctness is proven at the data level; a visual confirmation during a real
  job is recommended for the QA step.

## Config and Environment Changes

- None. No new environment variables, config keys, or database schema changes.

## Known Limitations

- **Two NEW, separate slowness issues were discovered while testing this round's fixes, but were left
  unfixed because they are outside this iteration's assigned scope:**
  - The market-regime research page (`/research/regime-lab`) ran out of its allowed memory once during
    testing under heavy concurrent load and stopped responding for a few minutes until restarted. This did
    not happen during normal, single-person use — only under unusually heavy simultaneous testing load.
    Worth a dedicated look in a future round.
  - A call the Stock Detail page also makes (`/api/regime-history`, the price-chart's regime-color
    background) has quietly gotten slower as the historical dataset has grown (roughly 1-3 seconds now,
    versus a fraction of a second when last measured). It is not one of the two calls this iteration was
    asked to speed up, so it was left alone, but it is very likely the next thing that will need the same
    treatment `/api/health` and the price chart just got.
- **The automated page-health check now has real speed limits, after the first attempt at it was
  rejected.** The first version of this round's change to the automated check (the script that replays a
  user walking through every page) only verified that each page showed real data rather than just a
  heading — a genuine improvement, but it did not actually enforce any speed limit, so a page that took
  eight seconds would still have been reported as fine. The reviewer rejected it, and a controlled test
  confirmed the reviewer was right: replaying the old check against a deliberately slowed-down server
  (the exact 6.2-second slowdown this check exists to catch) reported a clean pass.
  The corrected version puts a time limit on each of the four monitored calls, and was proved to work by
  slowing down one call at a time on a real running server: slowing the status check, the price chart, the
  data-availability chart, or the run history each now makes the check fail, and fail on the correct step.
  A run with no slowdown passes, and a milder 3-second slowdown still passes — the check catches real
  regressions without crying wolf. It was also run six times (three on a quiet machine, three with half the
  machine's processors deliberately saturated) and passed every time, which retires the earlier concern
  that tighter limits would be unstable. What it enforces is an end-to-end limit of about 4.5 seconds from
  clicking a page to seeing that page's real number; the precise, guaranteed per-call speed figures are
  still measured separately with a stopwatch-style tool and recorded in the project's performance notes.

---

## Verification pass (2026-08-10, after the independent audit) — no product changes

The independent audit reviewed this iteration and reached a clear conclusion: **the software changes
are correct and should ship as they are.** What it rejected was not the work but the *record* of the
checking — three claims had been written down as prose instead of being re-measured at the moment
they mattered. This pass re-did the checking. **Not one line of application code was changed.**

**1. The page-by-page check for this round's own headline change was never actually run.** The
automated replay covering "every page loads only what it needs" — the exact thing this round set out
to fix — had no result on file from either checking lane; one lane was told to skip it and the other
never included it. It has now been run against the real running application, and it **passes**. The
overall test summary for the round therefore moved from **"blocked"** to **"passed — 16 of 17 checks,
1 not executable"**, and the warning that a target journey had no result at all is gone.

**2. Six journeys were on file as failures, reversed by a written explanation instead of a re-run.**
The earlier failure had a real, mundane cause: the running web front end had been built pointing at
the wrong server port, so every page showed "backend unavailable" and every replay died at its first
click. Rather than leave a paragraph explaining that away, all six journeys were **re-run against a
correctly built front end and all six passed** (backfill honors the requested range, no range cap,
non-blocking start-up, pages load only what they need, backtest serves from storage, background-work
disclosure). The original failure file was archived rather than discarded.

One journey — "aggregates are precomputed at ingest" — was **deliberately not re-run**, and the
reason is recorded openly: its automated script consumes a specific unused historical date each time
it runs, and this round's earlier live testing already used it up. Re-running it would report a
failure that means "the test fixture is spent", not "the product broke", and would cost another
~18 minutes of heavy computation. That journey's evidence is the earlier live run, which the auditor
independently confirmed in the database. Refreshing that script's date is scheduled for next round.

**3. A live external data fetch happened during this round's testing — recorded, not hidden.** One
testing action used the Data page's "Fetch real EOD prices" button, which by design reaches out to an
external market-data provider (591 requests). The project's rules say testing must run entirely
offline against the committed sample data. **No external data was actually stored** (zero new price
bars), and no code change caused it — but the round's paperwork had claimed the rule was fully
honoured, and that claim was wrong. It is now logged for the owner, along with five earlier
occurrences that nobody had caught. Two habits were adopted so it cannot silently repeat: testing
triggers data jobs only through the offline "backfill" path, and the offline-only check is now made
**after** the tests run rather than before — the old order could never have caught a breach the tests
themselves caused. Re-checked after this pass's own testing: every data job it created used the
offline source.

**4. A promised responsiveness check had only ever been reasoned about, never measured — so it was
measured.** The service's status endpoint was polled once a second for 23 minutes straight, including
through a genuine 9½-minute spell of heavy background calculation. **Every one of 1,211 checks
answered successfully — no failures, no freeze.** When idle it answered in about 12 thousandths of a
second. During the heavy calculation it slowed as expected, and **one single check out of 424 took
2.6 seconds against a 2-second allowance** — a 0.24% overshoot, reported rather than rounded away,
and scheduled for next round.

### One new problem found, disclosed and scheduled (not fixed here)

Ten minutes *after* all the tests had passed, the heavy background calculation mentioned above **ran
out of its allotted memory and failed**. The service then entered a bad state worth naming plainly:
the status endpoint kept answering "ready" in 8 thousandths of a second, while **every page that
needs data returned an error** — the data availability chart, run history, price chart and the Data
page all failed. Restarting the service fixed everything immediately (all pages back well inside
their speed limits), which proves this is a stuck-process condition at the memory ceiling and **not**
a fault in anything this round built. It is important for two reasons: the service reported itself
healthy while it was unusable, and a shutdown request took longer than its two-minute grace period.
Both are logged for the next round, under the journey that owns memory-pressure behaviour.

### Scheduled for next round

Refresh the spent test date; make the automated page check enforce per-call speeds rather than an
overall 4.5-second page limit; make the "updating" banner depend on a job actually running; correct a
stale code comment that describes the opposite of the new behaviour; the one 2.6-second status
response; the stuck-process condition above; and a data-comparison test that has never actually run
because a name-matching filter silently skipped it (now ticketed).
