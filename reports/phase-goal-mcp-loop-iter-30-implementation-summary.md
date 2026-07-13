# goal-mcp-loop-iter-30 — Implementation Summary

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** developer

---

## Features Implemented

- **Pre-registration registry page**: a new page (`/research/registry`, reachable from the Research hub
  in one click) lists every hypothesis the system has ever registered or tested — what it claims, why
  someone believed it might work, when it was registered, where it came from, and its current status. It
  is populated with 11 historical entries covering everything the system has tried so far.
- **Machine-enforced pre-registration**: the automated process that certifies a new claim now checks it
  against this registry FIRST. If a claim doesn't exactly match something already registered, it is
  refused immediately — before any statistical test runs, before anything is written anywhere. This makes
  it structurally impossible for a future automated iteration to quietly test an unregistered idea and
  only "discover" it after the fact (a well-known way statistical results get faked, even by accident).

## Changed Behavior

- **The certification process (invisible to end users, only affects future automated iterations)**: the
  step that certifies a new claim now has an extra check in front of it. Today this check changes nothing
  observable — no current or upcoming automated iteration is submitting a new claim, so nothing is
  blocked. Its effect is entirely forward-looking: any FUTURE claim must be registered first, or it gets
  refused with a clear explanation.

## Backend-Only Items

None. Every backend addition (the registry data, the API endpoint, the gate check) has a corresponding
UI: the data and endpoint are directly visible on the new `/research/registry` page, and the gate check's
effect (refuse/proceed) is a backend-only mechanism by nature — it has no UI because it's not something a
user interacts with; it protects the integrity of what eventually shows up as "Proven" elsewhere.

## Incomplete Items

- The phase spec asked for "at least 14" historical entries in the registry. The actual, correct count is
  **11**. This is not a shortfall — it's the correct number once duplicates are properly merged. The
  system's history contains 14 raw test records across its two internal tracking files, but 3 of those
  are the exact same idea tested twice (once in an early exploratory pass, once again when it was formally
  promoted) — so they collapse into 1 registry entry each. All 14 original records are accounted for; none
  were dropped. This was verified programmatically, not just asserted.
- A short guided walkthrough video/script of the new page is expected to be produced by a later step in
  the pipeline (not part of building the feature itself).
- A human clicking through the actual page in a browser has not yet happened — that is the next
  pipeline step's job. Everything was verified by directly querying the running application (same data,
  same code path, just not through a mouse).

## Config and Environment Changes

- New setting: where the registry's historical record lives on disk, and whether the enforcement check is
  turned on. It has been turned ON as part of this change, after confirming the historical data behind it
  is complete and accurate.
- One new environment variable name was added to the list the automated pipeline already passes around
  internally (alongside two similar existing ones) so the enforcement check and the page always read the
  exact same file.

## Known Limitations

- The registry only knows about the 11 hypotheses tested so far. If the system tries something new in the
  future, someone (or an automated process) needs to add it to the registry BEFORE it can be certified —
  this is intentional (it's the whole point), not a bug, but it does mean the registry needs upkeep as the
  system grows.
- This iteration touches only the "front gate" of the certification pipeline. It does not change how
  claims are actually tested, does not touch any existing test results, and does not change any number
  currently shown to users as "Proven" or "Not yet proven" anywhere in the product — verified directly
  (the existing evidence page's data was confirmed byte-for-byte unchanged before and after this work).
