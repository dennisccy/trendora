# goal-ops-hardening-iter-8 — Implementation Summary

**Phase:** goal-ops-hardening-iter-8
**Date:** 2026-07-21
**Written by:** developer

---

## Features Implemented

- **Memory-pressure-aware backing-off during data ingest:** when the app is refreshing its cached
  numbers after a data import (backfill/rebuild), each of the four background "warm-up" steps
  (coverage snapshots, market phase, forward-return aggregates, and evidence drawdown expectations) now
  recognizes the specific case where the app is running low on memory and stops that one step early
  instead of continuing to push harder — rather than treating "ran low on memory" the same as any other
  minor per-item hiccup (which used to make it try the next item anyway, digging the hole deeper).

---

## Changed Behavior

- **Behind-the-scenes data refresh after an import:** Previously, if one of the four background
  refresh steps ran low on memory partway through, the app would log it and immediately try the next
  item anyway — repeatedly, under the same pressure, which is what caused the app to become
  unresponsive for several minutes during a real heavy data-loading session (confirmed in the prior
  iteration's testing). Now, the very first time one of those steps runs low on memory, it stops
  attempting further items in that one step, cleans up the memory it can, and moves on to the next
  independent step — so one step running low on memory no longer snowballs into the whole app freezing.
  Nothing about the *numbers themselves* changed — a refreshed value is still exactly what a fresh
  computation would produce; only how the app behaves when it hits a memory wall changed.

---

## Backend-Only Items

None — this iteration is entirely internal error-handling behavior inside an existing backend process
(the data-import "finalize" step). There is no new UI, no new endpoint, and no new information for users
to see; the user-visible effect (once fully confirmed — see "Known Limitations" below) is that the
top-bar "backend status" indicator should never go silent for minutes during a heavy data-loading job.

---

## Incomplete Items

None — the live proof-of-fix under real conditions (see below) has since been completed and passed.

**Update:** the phase spec required actually reproducing the original problem scenario live (starting a
real backend, running a full historical rebuild immediately followed by another heavy data job in the
same session, and watching memory usage and the status indicator throughout) to prove the fix holds
under real load. This developer session initially declined to run that live proof, because it is the
exact scenario documented as coinciding with the physical computer hard-resetting itself earlier the
same day, and running it again without confirmed human-supervised safety checks was judged too risky.
The team subsequently ran those safety checks (with a person present, watching the machine's
temperature) and confirmed they hold, then explicitly authorized re-running the live proof under active
monitoring. It was re-run and **passed cleanly**: two full heavy data-loading jobs back-to-back in the
same running backend, zero memory errors, the status indicator stayed responsive throughout (no silent
minutes), and the machine's temperature stayed well within safe limits the whole time (peak ~89°C
against an 95°C abort threshold) — no repeat of the earlier hardware reset. Full numbers are in
`reports/perf-budgets.md`.

---

## Config and Environment Changes

None. No new environment variables, config file fields, or database migrations. The existing memory
ceiling (`memory_cap_mb`, already set to 6144 MB) is unchanged — this fix makes the app stay comfortably
under that ceiling rather than raising the ceiling itself.

---

## Known Limitations

- **Unrelated to this fix, but discovered while testing:** there's a small, pre-existing bug in one
  unrelated automated test (about how backend log files are checked) that has nothing to do with this
  iteration's memory work — it was already there before this iteration started. It's noted for the team
  but intentionally not touched here, to keep this iteration's change small and focused.
- **A separate, already-known issue is intentionally not addressed here:** a different memory problem on
  the "backtest" page (unrelated code path, happens when a user views that page, not during data
  loading) was flagged in the previous iteration and is intentionally saved for a future iteration, so
  this one stays focused on a single, well-understood fix.
- **Physical hardware note (context, not caused by this iteration):** the team's computer running this
  project has twice reset itself instantly under very heavy data-loading load in the past two days — a
  hardware issue, not something this software fix by itself is guaranteed to solve. The team has since
  added safety limits (capping how many processor cores/threads heavy jobs use) as a precaution. This
  iteration's fix addresses the software-side memory problem; the hardware safety limits are a separate,
  already-in-place precaution.
