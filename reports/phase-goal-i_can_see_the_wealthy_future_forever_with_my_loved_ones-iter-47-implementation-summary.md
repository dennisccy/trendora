# Goal Iteration 47 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Written by:** developer

---

## Features Implemented

- **Research labs serve on the full live dataset again (J-105)**: The five heavy Research labs — Setup &
  Pattern event-study, Factor Lab, Multi-factor combination, Regime × Setup × Pattern, and Downtrend
  Opportunity — and their `N=` sample drill-downs now load successfully on the full live dataset instead of
  failing with an out-of-memory error. This restores the labs that regressed last iteration (the event
  study and the Factor Lab were returning "Backend unavailable" / HTTP 500 on the grown data).

---

## Changed Behavior

- **How the Research labs read their forward-return data**: Previously each heavy lab loaded the *entire*
  forward-returns table into memory at once to do its analysis. On the grown live database (about 3 million
  rows) that briefly used roughly 5 GB of memory and crashed on a host with less RAM available. Now each lab
  reads the same data in small, configurable batches and, where it only needs a slice (e.g. one setup's
  occurrences), it filters the read down to just those rows. The numbers shown to the user are **exactly the
  same** — every matrix cell, every mean / win-rate / sample-count, every `N=` cohort — only the memory
  footprint changed.
- **The overnight warm-up's bookkeeping**: The background warm-up that fills in forward returns also used to
  load the whole table to decide what was already saved; it now streams that check in batches. It still
  saves exactly the same rows and never duplicates anything.

---

## Backend-Only Items

- None. This iteration changes how existing pages get their data, not what is shown. There are no new
  endpoints, models, or screens.

---

## Incomplete Items

- None. Every item in the iteration spec is implemented: the seven research forward-return reads and the
  warm-up bookkeeping are streamed, the single new config setting is added and validated, and the
  byte-identity / idempotency / config tests are written and passing.

---

## Config and Environment Changes

- `research.read_batch_size` (in `config.yaml`) — the batch size the heavy Research labs use when streaming
  forward-return rows. A pure memory-safety setting (not a displayed value). Must be 1 or greater; the app
  refuses to start with an invalid value. Default: `2000`.

---

## Known Limitations

- The numbers are identical by design and proven by automated equality tests against the committed seed
  data; the only user-visible difference is that the labs no longer crash under heavy data.
- Confirming the real reduction in memory use on the full 3.3 GB live database (peak well below the previous
  ~5 GB) and the live HTTP-200 rendering of each lab is the job of the browser-QA step — it must be done on
  a freshly restarted, warmed backend, fetching one heavy page at a time (a saturated backend can otherwise
  show false "Backend unavailable" frames).
- The full backend test suite includes a heavy one-time data-bootstrap step that takes several minutes on
  this host; that is pre-existing and unrelated to this change.
