# goal-ops-hardening-iter-33 — Implementation Summary

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **The frontend launcher now actually serves production mode.** For the entire session so far, the
  script that is supposed to start the website in "production mode" for measurement and automated checking
  was silently starting it in "development mode" instead — a bit like a store owner turning on the
  "closing sale" sign but never actually running the sale. Development mode is slower and compiles pages
  on demand, so any speed measurement taken against it would have been meaningless. This iteration fixes
  the launcher so it builds the website for real (only when needed) and then serves the real, fast,
  production version — the same thing a live deployment would run.
- **A one-time check before starting**: the launcher now checks whether the existing built copy of the
  website is up to date. If it's missing or out of date (because code changed since the last build), it
  rebuilds first. If it's already current, it skips the rebuild and starts immediately — no wasted time.
- **If a build genuinely fails** (for example, a real code error), the launcher now stops cleanly, shows
  the real error, and does not silently fall back to the old "development mode" behavior or leave a broken
  half-started website running.
- **A small, unrelated reporting-tool fix rode along**: a report-merging tool used internally by the
  automation pipeline could, in one narrow situation, quietly turn a real test failure into an apparent
  "pass" in the merged report. That has been fixed and is now covered by an automated check that would
  catch the old bug if it ever came back.

---

## Changed Behavior

- **Starting the frontend for automated checks**: Previously, running the frontend launcher always started
  the website in "development mode" (used while actively coding — slower, with extra debug behavior).
  Now, it builds the website for real (if needed) and serves it in "production mode" (the same speed and
  behavior real users would see). This only affects how the site is launched for automated
  testing/measurement — day-to-day development (`npm run dev` style workflows) is untouched.

None if no existing behavior changed — n/a, see above.

---

## Backend-Only Items

None — this iteration touched launcher scripts and one internal reporting tool, not the backend
application itself.

---

## Incomplete Items

- **The formal, dated speed measurement** (how fast each of the 11 main pages loads in a real browser, and
  how fast each page's data loads) is intentionally handled by the next automated QA step, not by this
  implementation step. This iteration's job was to make sure the website is actually being measured
  correctly (in real production mode) — the actual measurement run and its recorded numbers come next.
- Two follow-up items from the ongoing hardening work are intentionally deferred to the next iteration (not
  part of this one's scope): recording how long a health check takes under sustained load, and a controlled
  test of what happens if the system runs low on memory during heavy background work.

---

## Config and Environment Changes

- No new required environment variables. One existing, already-documented environment variable
  (`NEXT_DIST_DIR`) is now also used internally by the new automated tests to build into a temporary,
  throwaway location instead of the real one — this has no effect on normal operation.

---

## Known Limitations

- A small, internal side-effect was discovered and worked around: building the website for a
  never-before-seen internal build location causes a project settings file
  (`apps/frontend/tsconfig.json`) to be automatically rewritten by the website-building tool itself. The
  new automated tests account for this and always restore the file afterward, so it never leaks into the
  committed project files. This is a pre-existing quirk of the website-building tool, not something
  introduced by this change, and it does not affect the real, normal way the website gets built and served.
- One existing, unrelated backend query (used by the "Data Coverage" page) reads across the full price
  history to build a small summary table. This is a standard, efficient kind of database summary query
  (not the "load everything into memory" pattern the project explicitly guards against) and was already
  present before this iteration — flagged here only for transparency, not as something newly introduced or
  in need of a fix right now.
- The real backend and frontend services were started and left running (on their usual internal ports) so
  the next automated QA step can measure against a live system, exactly as this iteration's task required.

---
---

# Fix Pass — after QA returned FAIL (2026-07-29)

Everything above describes the first pass. Quality Assurance then re-checked the work in a real browser and
returned a **FAIL** with two blockers. Both were fixed. This section covers only what changed since.

## Features Implemented (fix pass)

- **An honest "still computing" message on the Research → Regime Lab page.** That page is fed by a figure
  set the system works out once per data set, across the whole stored history. The very first time anyone
  opens the page after new data arrives, that calculation genuinely takes about one to one-and-a-half
  minutes. Until now the page showed nothing but a grey shimmering placeholder for the whole of that wait,
  with no explanation and no way out — QA could not tell "still working" from "broken", and rated it a
  high-severity, user-facing defect. The page now shows, after a three-second grace period, a clearly
  labelled card stating what is happening, how long it has been going ("Still computing — 42s elapsed"),
  that this only happens on the first read after a data change, and that the table will appear by itself.
  Nothing partial or invented is displayed in the meantime, and the counter is the page's own measured
  wait — never a guessed finish time.

- **A Retry button when that page's data cannot be loaded.** If the read fails, the existing
  "Backend unavailable" card now carries a Retry control that re-runs the read in place — no page reload,
  and the person's current view settings are kept.

## Changed Behavior (fix pass)

- **Regime Lab page, slow first read:** previously an unlabelled grey placeholder for as long as it took
  (QA observed 40+ seconds of total silence). Now a plain-language, time-stamped explanation after three
  seconds.
- **Regime Lab page, failed read:** previously an error card with no action. Now the same card offers Retry.
- **Regime Lab page, normal (fast) read:** unchanged, and the figures shown are identical. Nothing about
  how the numbers are produced or fetched was touched.
- **Every other page:** unchanged.

## What was fixed in the automated checks (not a product change)

QA's second blocker was that the three new start-up-script tests all timed out and, worse, had left debris
behind in the project's source files — including a deliberately-broken file that would have failed the next
real build. Two separate causes, both in the test code (the start-up script itself was correct and had
already been approved in code review):

1. **The time limit was too tight.** The tests allowed five minutes for a full app build. That is generous
   on an idle machine (the builds actually take 20-40 seconds) but not while the live services are running.
   The limit is now fifteen minutes and can be adjusted per machine, and a failure now reports the build's
   own log and says which setting to raise instead of just "timed out".
2. **The clean-up could not survive being killed.** An earlier run was terminated outright mid-build, so no
   clean-up code ran at all and the debris was left behind; the next run then failed instantly on its own
   safety check. Clean-up now also runs at the *start* of every run, so a run that was killed repairs the
   damage on the next attempt rather than blocking it. Launched processes are also now owned by the test
   framework itself, so a failing check can never leave a stray web server running on a shared port.

## Incomplete Items (fix pass)

- **The slow first calculation itself was not made faster.** This fix makes the wait honest and escapable,
  not shorter. The durable remedy — computing that figure set in the background when the service starts, so
  nobody ever waits for it — is a backend change this iteration's brief explicitly rules out of scope.
  Recommended for a future iteration.
- **The other Research lab pages still show a bare placeholder while loading.** Their reads are much faster
  today and none was named in the QA failure list, so they were deliberately left alone. The new shared rule
  is written so they can adopt it later.
- **One error QA saw once was not reproduced.** During QA's cold testing, one of two attempts came back as a
  raw server error instead of data. On this pass the same request answered normally in under a third of a
  second. Reproducing it would mean deliberately clearing the stored result and running two heavy
  calculations simultaneously — a heavy-load event this iteration's brief does not cover and the machine's
  hardware-protection rules discourage. Recorded as an open observation. Note that such an error now reaches
  the user as the retryable error card rather than as a page that hangs silently forever.

## Config and Environment Changes (fix pass)

- `TRENDORA_FRONTEND_BUILD_TIMEOUT_S` — how long the start-up-script tests wait for a full app build before
  giving up — default: `900` (seconds). Test-only; does not affect the running product.
- `TRENDORA_FRONTEND_START_TIMEOUT_S` — how long those tests wait for the app to start when no build is
  needed — default: `120` (seconds). Deliberately short, because that path is supposed to be fast.
- No database migration, no new secret, no new external service, no `config.yaml` change, and no change to
  the machine's hardware-protection settings or the scripts that carry them.

## Verification performed (fix pass)

- Start-up-script tests: **3 passed in 121 seconds** (previously 3 failed in 641 seconds).
- New front-end unit tests for the loading/error rule: **13 passed** (proven to fail before the fix existed).
- Report-merge self-test: **7 passed**.
- All 8 stored user-journey scripts replayed against the rebuilt production-mode site: **8/8 passed**.
- All 11 main pages plus the Research hub and two sibling lab pages: all returned HTTP 200.
- The three Regime Lab states (slow wait, failure + Retry, normal load) were each confirmed in a real
  browser and captured as screenshots under `reports/qa/goal-ops-hardening-iter-33-evidence/`.
- After the test run: no leftover files, no leftover processes, and no unintended changes to project files.
- The backend (port 8255) and the production-mode frontend (port 3255) were left running for the next
  automated QA step.
- The full backend test suite was deliberately not run: on this project's 30-year data basis it takes
  roughly 10-11 hours, and no backend application code changed in this iteration.
