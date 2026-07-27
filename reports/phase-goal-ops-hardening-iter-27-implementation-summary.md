# Phase goal-ops-hardening-iter-27 — Implementation Summary

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Written by:** developer

---

## Features Implemented

This is a hardening/reliability iteration. It does not add anything new for the operator to use — it
closes two bugs found during the previous iteration's own testing, on features that already existed.

- **Backtest page no longer crashes under a race.** If two people (or two browser tabs, or a person and an
  automated check) both ask to view the Backtest evidence for the same never-before-viewed historical date
  at almost the same moment, the backend used to occasionally return an error page to one of them. Both
  requests now always succeed.
- **Data Manager page tells the truth when its "coverage" numbers are momentarily behind.** Under a rare,
  specific sequence of events, the Data Manager page's "Dataset coverage" panel could show
  "— → —" / "Universe: 0" for a database that actually has years of real data in it — a misleading blank
  reading. It now shows the real, correct prior numbers along with a plain-language note: "Coverage as of a
  prior scan (version X) — refreshes on the next data job." This never happens for a genuinely brand-new,
  empty database — that case still shows the honest all-zero state it always has.

---

## Changed Behavior

- **Data Manager coverage panel**: Previously, whenever the panel's internal "which numbers are current"
  check missed by any margin, it silently fell back to an all-zero, blank-looking display — indistinguishable
  from "this database has never been scanned." Now it distinguishes three cases and labels them: numbers are
  current, numbers are a real (slightly out of date) prior reading, or the database genuinely has nothing yet.
- **Backtest evidence request under a race**: Previously, a very specific timing collision between two
  simultaneous requests for the same brand-new historical date could surface as an unhandled server error.
  Now that collision is caught and resolved silently — both requests succeed, and no duplicate data is ever
  written.

---

## Backend-Only Items

None — the one new piece of information (the "coverage as of a prior scan" label) is wired all the way
through to the Data Manager page.

---

## Incomplete Items

None from this iteration's scope. Everything listed in the phase spec was built and verified.

---

## Config and Environment Changes

None. No new environment variables, config keys, or migrations.

---

## Known Limitations

- This fix does not change how fast a genuinely NEW (never-before-viewed) historical Backtest date loads —
  that can still take on the order of a minute for a very old date on the full 30-year database, which is a
  separate, already-known, deliberately out-of-scope item for this iteration (the owner has an open decision
  about whether that should have its own performance budget).
- One unrelated, pre-existing documentation issue was noticed but not fixed (out of scope): the project's
  `.claude/project-template.md` configuration file still contains the generic starter template rather than
  this project's actual settings. It did not block this iteration's work (the real commands live in the
  project's README instead), but a maintainer should eventually fill it in properly.
- A full browser-based QA pass (re-confirming all the still-passing existing features look and work
  correctly) was intentionally left for the next pipeline stage, per how this pipeline splits work between
  the implementer and the QA reviewer. The implementer did independently verify both fixes work using a real,
  live, two-at-once request test against the running application (not just automated unit tests) before
  finishing, including a real screenshot of the new coverage label.
