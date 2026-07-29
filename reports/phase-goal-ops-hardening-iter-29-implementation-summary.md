# goal-ops-hardening-iter-29 — Implementation Summary

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-27
**Written by:** developer

---

## Features Implemented

- **The Evidence page can no longer run the backend out of memory.** The page that shows which of
  Trendora's scoring signals have been statistically proven ("Evidence") was reading a growing pile of
  historical data into a single in-memory structure every time it computed one part of the page (the
  "historical drawdown & dry-spell expectations" panel on each claim's card). As the price history grew,
  that structure grew with it, without limit. It has been rewritten to process the data in small, fixed-size
  batches instead, so the memory it uses no longer grows as more trading history accumulates.
- **A single stuck claim can no longer take down the whole Evidence page.** If the computation behind one
  claim's "expectations" panel fails for any reason, the page now shows every OTHER claim normally and
  marks only the failing one with a small, calm note ("Unavailable — monitored and refreshed as new data
  arrives.") instead of the failure breaking the page for everyone.

---

## Changed Behavior

- **The Evidence page's "drawdown & dry-spell expectations" panel**: Previously, if the underlying
  computation for one claim ran out of memory, the entire page's data request could fail (returning an
  error to the browser). Now, that one claim's expectations panel is replaced with a short, factual notice,
  while every other claim on the page renders exactly as before.
- **No change to what is shown when a claim genuinely has no applicable history** (e.g., a claim whose
  underlying selection criteria don't match any stored data) — that case still renders nothing for the
  panel, exactly as it did before this change.
- **No change to any score, ranking, or "proven" status** anywhere in the product. This iteration only
  changes how much memory one specific background calculation uses and how a single failure in that
  calculation is displayed — it does not change any numbers.

---

## Backend-Only Items

None — the one new piece of backend behavior (the "unavailable" failure state) is wired all the way through
to a visible note on the Evidence page.

---

## Incomplete Items

None from this iteration's scope. Everything listed in the plan (the memory-bounding fix, the failure-
isolation guard, the new frontend field, the new tests) was implemented and passed its tests.

The following were explicitly OUT of this iteration's scope from the start (named in the plan, not
overlooked):
- Two similar-but-separate calculations elsewhere in the Research pages carry the same theoretical risk but
  have not actually caused a problem yet — left for a future, separate fix so only one risky change ships
  at a time.
- Live, in-browser verification of the full page (does it load fast enough on the real dataset, does a
  visual screenshot show the new "Unavailable" note, does the automated regression check pass) is the next
  pipeline step's job (reviewer/QA), not this one. This developer did do a live, informal check by hitting
  the underlying data endpoints directly (not through a browser) against the real, live database — see
  "Known Limitations" below for what that did and did not prove.

---

## Config and Environment Changes

None. No new environment variables, no new config file keys, no database migration. The fix reuses an
existing config value (the batch size the page's data reads already used) instead of introducing a new
setting.

---

## Known Limitations

- The new "one claim shows a calm failure note instead of breaking the page" behavior was proven with
  automated tests (both backend and frontend) but was NOT observed visually in a real browser this
  iteration, because on the live database every claim currently computes successfully — there was nothing
  to fail. The next pipeline step (QA) is expected to force this state (e.g., with a simulated failure) and
  capture a screenshot if a visual walkthrough is required.
- A live "add one day of new historical data" test (which would also exercise this same memory-safety fix
  from the ingest side) was intentionally left for the QA step, per the plan, rather than run twice by both
  developer and QA.
- This developer's live checks against the real database did confirm the core claim: hitting the Evidence
  page's data endpoint returned all 7 real evidence claims correctly and quickly (77 milliseconds), and a
  separate, much heavier calculation on the Research pages that shares the same underlying fix completed
  successfully against a pool of over 750,000 historical data points with no crash and no out-of-memory
  error — both were previously the exact site of past crashes on this project.
