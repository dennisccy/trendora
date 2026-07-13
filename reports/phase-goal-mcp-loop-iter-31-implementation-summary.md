# goal-mcp-loop-iter-31 — Implementation Summary

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Written by:** developer

---

## Features Implemented

- **Negative-results graveyard page**: a new page (`/research/graveyard`, reachable from the Research hub
  in one click) lists every idea the system's statistical referee has REJECTED — every claim that failed
  its out-of-sample test, or didn't have enough data to judge either way. Today that's all 14 ideas the
  system has ever tested (7 from the main track, 7 from an internal exploratory track), shown with what
  was tested, when, the exact reason it was rejected, and — where known — which registered hypothesis it
  traces back to. The one idea that is permanently retired (a moving-average pattern that failed twice) is
  visibly flagged "permanent."
- **A visible re-test rule**: the same page explains, in one place, exactly what it would take to re-test
  a rejected idea (in short: a genuinely new reason to believe it, registered as a brand-new attempt — a
  rejected idea can never just be quietly re-run hoping for a different answer). Every row links to this
  explanation.
- **Internal exploratory failures made visible for the first time**: the system has always had two
  tracking tracks — a public one and an internal exploratory one used for early-stage research. Only the
  public track's results have ever been shown to users. This change makes the internal track's REJECTIONS
  (never its successes — it has had none) visible too, purely as a "here's what we already tried and it
  didn't work" record. Nothing about what counts as "Proven" anywhere else in the product changed.

## Changed Behavior

None. This is a purely additive page. Every other page, every number currently shown as "Proven" or "Not
yet proven," and every existing screen behave exactly as before — verified directly (the existing Evidence
page and Registry page were confirmed to return byte-for-byte the same data before and after this work).

## Backend-Only Items

None. The one new backend piece (a service that reads both internal tracking files and combines them) has
a direct, matching front-end page — the new `/research/graveyard` table is its only consumer, and shows
everything it produces.

## Incomplete Items

None from this iteration's scope. Everything the spec asked for is built: the page, the underlying data
service, the governance-hub link, and the link from a graveyard entry back to its registered hypothesis.

Two things remain, both intentionally out of this step's job:
- A short guided walkthrough of the new page is expected to be produced by a later pipeline step (not
  part of building the feature itself).
- A human (or an automated browser) actually clicking through the page has not happened yet — that is the
  next pipeline step's job. Everything here was verified by directly querying the running application
  (same data, same code path, just not through a mouse).

## Config and Environment Changes

None. This iteration reuses settings that already existed from an earlier iteration (where the two
tracking files live) — nothing new was added to configuration, and no new environment variable was
introduced (an existing one, already used internally by the automated pipeline, is now also read by this
new page's backend service).

## Known Limitations

- The graveyard only shows what has already been tested. It has no way to predict or list ideas that
  haven't been tried yet — that's expected; it's a record of the past, not a forecast.
- This page cannot be used to delete, edit, or quietly retry a rejected idea — there is no such button
  anywhere. That is deliberate: the whole point of this page is to make it easy to see what NOT to try
  again, and impossible to make a rejection disappear.
- The environment used to build this could not run one of the project's two automated test mechanisms for
  the front-end code (a pre-existing limitation of this particular machine's setup, not something this
  iteration caused — the same gap was already noted in the prior iteration's records). The other mechanism
  (which checks the code is internally consistent) ran clean, and the new page and data service were both
  exercised directly against the running application as a substitute check.
