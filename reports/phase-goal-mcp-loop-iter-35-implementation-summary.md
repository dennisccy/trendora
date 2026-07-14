# goal-mcp-loop-iter-35 — Implementation Summary

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** developer

---

## IMPORTANT — read before treating this phase as done

The code changes described below are finished, but the automated checks that would normally prove they
work (running the test suite, checking the frontend compiles, starting the app to confirm it boots) could
**not** be completed this session. Partway through, the tool this agent uses to run commands stopped
responding entirely — every command failed, including ones as simple as printing a word to the screen —
and it never recovered despite many retries over an extended period. The most likely explanation: earlier
test runs in this same session created several very large temporary database files (each one loads 30
years of price history for ~590 stocks — that's normal for this project's test suite, but expensive), and
the disk space set aside for temporary files for this pipeline run appears to have filled up.

Two small, harmless leftover files (`.iter35-diskprobe.tmp` and `.iter35-diskprobe2.tmp`) were created at
the project root while diagnosing this and still need to be deleted by whoever has command-line access
next.

**Bottom line for the operator:** treat this as "code written, not yet proven to work." The next step
should be re-running the standard checks (backend tests, frontend build, start the app) once the
environment is healthy again — not shipping this as-is. Two of the backend test files WERE actually run
successfully before the tool broke (58 tests total, all passing) — see "What was actually verified" below.

---

## What this phase adds, in plain terms

When someone fetches fresh price data from the live provider, it's possible — though rare — for that
provider to have silently gone back and revised history it already gave us (this happens when a stock pays
a dividend or splits; some providers recalculate the entire price history to account for it). Before this
phase, the platform had no way to notice if that happened. If the provider quietly changed a price for a
date the platform already had on file, the platform's own database wouldn't update (by design, to avoid
duplicate data) — so the discrepancy would go completely unnoticed.

This phase adds a watchdog for exactly that scenario:

- **Features Implemented**
  - **Live-vs-seed drift check**: every time an operator runs a "Fetch" job (pulling fresh price data),
    the platform now compares the last 20 days of overlap between what it just fetched and what's in the
    trusted, committed reference data. If anything differs — even by a single cent — it's flagged.
  - **New "Live-vs-seed drift" card on the Data page**: shows whether the most recent fetch matched the
    trusted reference data. If it didn't, the card lists exactly which stock(s) and which date(s) were
    affected, labeled as an "adjustment seam."
  - **Site-wide caution banner**: the platform already shows a small banner at the top of every page
    saying whether "today's board" can be trusted. That banner now also turns cautionary when a drift
    issue is detected, until the situation is resolved — so the warning isn't buried on one page, it's
    visible everywhere.

---

## Changed Behavior

- **The daily "is today's data trustworthy" check**: previously checked three things (is the service
  running, is the data fresh, are the internal records readable). It now checks a fourth thing (does the
  live data agree with the trusted reference) as well. If no fetch has ever revealed a discrepancy, this
  behaves exactly as before — nothing changes for a user who never triggers a live fetch.

---

## Backend-Only Items

None — the new drift-check capability is fully wired to a visible UI card (the "Live-vs-seed drift"
section on the Data page) and to the existing site-wide trust banner.

---

## Incomplete Items

- **Verification (test suite, frontend build, app startup check)**: NOT completed this session due to the
  tooling outage described above. This is the main open item — see "What was actually verified" below for
  the precise, honest breakdown of what is and isn't confirmed working.
- **Two related but separate checks from the same backlog card were intentionally left out of this
  phase** (as planned, not as a shortcut): comparing today's overall statistical patterns against
  historical norms, and a deeper "anomaly scanner" cross-check. Neither of those exists yet in any form, so
  they were correctly scoped out rather than half-built.

---

## Config and Environment Changes

- `TRENDORA_DRIFT_REPORT_PATH` — optional override for where the drift report file is stored. Not needed
  in normal operation (has a sensible default location).
- `config.yaml` — new `data_quality.drift` section: the check is on by default, compares the last 20 days
  of overlap, and can be switched off entirely as an emergency escape hatch if it ever needs to be
  disabled without a code change.
- `config.yaml` — the existing "how serious is each kind of problem" list now includes this new drift
  check, set to the same "proceed with caution" severity level as a stale-data warning (one level below
  the most severe "do not trust this at all" level).

---

## Known Limitations

- **Not yet verified by an actual test run** — see the top of this document. This is the single most
  important caveat: the code has been written and carefully re-checked by reading it closely, but "reading
  code carefully" is not the same guarantee as "the tests actually passed." Please run the test suite
  before relying on this.
- **This only catches one specific problem** (a provider quietly revising history for dates we already
  have on file). It does not yet catch a provider's overall statistical patterns shifting in a way that
  doesn't show up as an exact date-by-date mismatch — that's planned as a separate, future addition to the
  same watchdog, not something this phase claims to cover.
- **The check only runs when someone actively fetches fresh data.** It does not run on a schedule by
  itself; it's a byproduct of the Fetch action a user or operator already performs. If nobody ever fetches
  fresh live data, this new capability sits quietly and does nothing (which is the correct, honest
  behavior — there's nothing to check yet).
