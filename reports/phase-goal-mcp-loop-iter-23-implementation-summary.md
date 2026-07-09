# goal-mcp-loop-iter-23 — Implementation Summary

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Written by:** developer

---

## Features Implemented

- **None.** This iteration built no new product features. Its entire purpose was to re-check work that
  was already built in the previous iteration (deep 30-year benchmark lines and honest data-source
  labels on the Dashboard chart, plus a new panel on the Data page listing where each benchmark's price
  history comes from) through the project's formal browser-testing process, because that formal check
  had gone stale after a last-minute bug fix. Nothing the user sees is new as of this iteration; what
  changes is that the previously-built capability is now formally confirmed working, clearing a
  process-level "not yet formally verified" flag.

---

## Changed Behavior

- None. No product behavior changed. One internal test script was updated to expect the correct current
  count of tracked market symbols (590, up from 587) — this reflects a count that already changed in the
  previous iteration; the test script had simply not been updated to match yet.

---

## Backend-Only Items

- None. No backend code changed.

---

## Incomplete Items

- **The formal backend test confirmation this iteration exists to obtain is now complete, and it
  surfaced one genuine pre-existing test failure that is not fixed in this pass.** Both automated backend
  test runs were re-run using a technique that survives long waits, and both ran all the way through this
  time (roughly 2.5-4.5 hours total, which is expected and normal for this product's 30-year test basis —
  the test-runner project as a whole is known to take many hours for its full suite; this was only the
  targeted subset). Results:
  - The first batch (6 test files covering data management, price caching, and the evidence/scoring
    ledger) came back **fully clean: every one of 146 checks passed, zero failures.**
  - The second, more expensive test file (12 checks covering the `/api/indexes` endpoint that serves the
    deep benchmark data) came back **11 of 12 passed, 1 failed.** The one failure is a narrow, technical
    edge case: when a very old date is requested together with a "show full history" option, one specific
    benchmark series (the interest-rate proxy `^TNX`, which only has price history going back to 2021,
    much shorter than the other 30-year benchmarks) is missing from one internal comparison the test
    makes. Investigation traced this to a genuine gap in either the test itself or the underlying serving
    logic for that narrow combination of options — it has existed, unnoticed, since the benchmark data was
    added two iterations ago, because this particular test had never actually finished running before
    (it kept getting cut off early, the exact evidentiary gap this iteration exists to close). It has
    nothing to do with anything changed in this iteration. It also does not appear to affect what a user
    actually sees on the Dashboard's default view (the two checks that directly cover that default view
    both passed) — but that connection needs an explicit sign-off from the next review step, not just this
    developer's read of it, and is not something this step is authorized to change.
- The remaining browser-based checks (does the chart visually show the deep 30-year line, do the labels
  read correctly on screen, etc.) are intentionally NOT part of this developer step — those are run by a
  separate, dedicated browser-testing step later in the process, using the live application (which will
  need to be started fresh — see Known Limitations).

---

## Config and Environment Changes

- None. No configuration files, environment variables, or database schema changed.
- One test fixture (a scripted browser-replay file used by the automated QA process, not something an
  operator interacts with) was updated to expect "590 symbols" instead of the outdated "587 symbols" on
  the Data page — this brings the test in line with a count that already changed last iteration.

---

## Known Limitations

- **One narrow, pre-existing backend test failure remains unresolved** (see "Incomplete Items" above for
  the full plain-language explanation). It affects a technical edge case in how one short-history
  benchmark series is compared internally by one automated test, not (as far as this step can tell) what
  users actually see. Fixing it would require changing backend source code, which is outside what this
  verification-only iteration is allowed to touch — it is left for the next review/decision step to
  triage: either wave it through as a pre-existing, narrowly-scoped, unrelated gap, or schedule a small
  dedicated fix in a future iteration.
- The application's backend and frontend servers are **not currently running** — they were running
  earlier in this step but stopped on their own between actions (a known quirk of how this automated
  session manages long-running processes, not something anyone did deliberately). The next automated
  step — the browser-based visual check — will need to start both fresh before it can proceed.
- No data, features, or other user-facing behavior are at risk from the above — this iteration touched no
  application source code at all, only a test-script expectation and verification bookkeeping.
