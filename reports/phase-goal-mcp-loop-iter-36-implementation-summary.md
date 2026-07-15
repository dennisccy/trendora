# goal-mcp-loop-iter-36 — Implementation Summary

**Phase:** goal-mcp-loop-iter-36
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **Referee audit page** (`/research/referee-audit`): a new read-only page that answers "is the statistical
  certifier itself trustworthy?" It shows two things: (1) how often the certifier would wrongly call a
  known-fake pattern "real" when tested against 200 deliberately meaningless signals, compared to how
  often it's supposed to make that mistake, and (2) whether the certifier catches an obvious "cheat" — a
  fake signal that is built by literally looking at the future outcome it's supposed to predict.
- **4th governance card on the Research hub**: a new "Referee audit" tile alongside the existing
  Pre-registration registry, Negative-results graveyard, and Certification-budget accounting tiles. This
  completes the planned set of four governance/process surfaces.
- **One offline calibration run**: the audit was actually executed once against the real product data as
  part of building this feature, and its result is what the page displays.

---

## Changed Behavior

- None. This is a purely additive feature — no existing page, score, or workflow changed behavior.

---

## Backend-Only Items

- None. Every backend piece (the calibration engine, its configuration, and the new API endpoint) has a
  corresponding page on the Research hub that a user can open and read.

---

## Incomplete Items

- None from this iteration's assigned scope. The next-cluster items (risk-analytics pages, a related
  "referee settings sweep" feature, and a housekeeping pass that batches together several already-verified
  checks) were intentionally left for future iterations, as planned.

---

## Config and Environment Changes

- New configuration block in `config.yaml` (`research.referee_audit`): controls how many "fake signal"
  trials the calibration check runs (200), a fixed random seed so the result is exactly reproducible, and
  where the result file is saved. None of these are things an end user sets — they're internal tuning
  values, and the defaults are already committed.
- New optional environment variable `TRENDORA_REFEREE_AUDIT_PATH` — lets an operator point the app at a
  different result file if needed; unset by default, so normal operation is unaffected.

---

## Known Limitations

- **The calibration result itself is imperfect, and the page says so honestly.** Out of 200 fake-signal
  trials, the certifier wrongly said "real" 16 times (8%) when it was supposed to make that mistake about
  5% of the time. That's a mild yellow flag, not a red one — with only 200 trials, an 8% miss rate could
  plausibly just be normal statistical noise around a true 5% rate. The page shows the exact number plus
  its uncertainty range so a person can judge for themselves. Nothing was tuned or adjusted to make this
  number look better — the whole point of this feature is to report the honest result, not to pass a test.
- **The "obvious cheat" test was NOT caught, and the page shows a bright red warning about it.** The test
  deliberately builds a fake signal that already knows the future answer it's being graded on — think of it
  like grading a multiple-choice test where the answer key was glued to the question sheet. Every
  statistics engine will call that fake signal a slam-dunk "real pattern," because — mathematically — the
  test can't tell the difference between a genuine, incredibly reliable pattern and one that's cheating by
  definition. This was expected as a real possibility, which is exactly why the page has a loud, impossible-
  to-miss red warning built in for this case, rather than silently showing a green checkmark. No other part
  of the product is affected — the real "which stocks look strong" scores and the real "proven / not yet
  proven" evidence page are completely separate from this check and remain exactly as they were before this
  feature (verified byte-for-byte identical).
- **The new page's history states (nothing run yet, a broken result file, "test passed cleanly") were not
  each individually checked in a live browser** — only the real "cheat not caught" result, which is what
  actually happened, was checked live. The other three visual states were built and automated-tested but
  not eyeballed in a browser window. If that matters for sign-off, it's a quick follow-up check for QA.
