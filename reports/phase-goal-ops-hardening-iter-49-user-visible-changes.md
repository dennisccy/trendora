# Phase goal-ops-hardening-iter-49 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** ui-impact-analyst

---

## Context

`plan.md` and the phase spec both set `Frontend Present: no`, and the dev handoff confirms zero files
under `apps/frontend/` were touched (`git log`/dev handoff's "Files Changed" list only names
`apps/backend/app/engine/{data_manager.py,forward_testing.py,research.py}`, four backend test files,
`reports/perf-budgets.md`, `runs/goal-session-ops-hardening/state/blueprint.md`, new evidence CSVs, and
`runs/goal-ops-hardening-iter-49/status.json`). Despite that, the phase spec's own "New user-facing
capability" and "Product surface delta" sections (not "None") describe a real, observable change to
already-existing pages — the SAME classification precedent iter-48 used in this session — so this is
scored as a genuine (if narrow, indirect) user-visible change, not a pure backend-only phase. No
component, page, label, field, or button was added, removed, or renamed anywhere.

This iteration is the direct continuation of iter-48: iter-48 fixed the FIRST slow finalize-tail step
(`coverage_membership_timeline_refresh`); iter-49 fixes the other TWO (`forward_aggregates_warm`,
`drawdown_expectations_warm`) that were still causing the OVERALL backfill job to miss the 20-minute
window even after iter-48 landed.

---

## What Users Can Now Do

- A historical-day backfill (any date earlier than the latest cached snapshot) now reliably reaches a
  genuine terminal outcome for its **entire** finalize tail — not just the one step iter-48 fixed — within
  the same ~20-minute window already advertised to the operator. Proven on 3 independent, real end-to-end
  runs: **1,012.71s / 1,048.22s / 1,044.77s** (≈16m53s–17m28s), comfortably inside the 1,200s (20-minute)
  budget. Previously, the job's status badge could keep spinning on "running" well past 20 minutes (in the
  worst case iter-48's audit recorded, it never finished at all).
- Because the whole job now reaches a terminal status reliably, a historical-gap date's backfilled
  snapshot becomes usable — clickable from `/scanner-runs`, viewable at `/scanner-runs/<runId>` — within
  the promised window, not only on a lucky run.
- Users viewing `/backtest`'s forward-return aggregate tables and `/evidence`'s "Historical drawdown &
  dry-spell expectations" panels are served numbers computed measurably faster server-side during the
  ingest warm step that feeds those caches (drawdown claims up to ~3.9x faster per claim; forward
  aggregates' per-observation accumulation also reduced). The displayed numbers themselves are unchanged —
  proven byte-identical to the pre-fix computation via 120+ new/existing automated tests — so the
  practical benefit is faster/more reliable ingest, not a different number on screen.

---

## What Changed in the Visible UI

- Nothing. Zero frontend files were modified this iteration; no new page, panel, route, button, field, or
  label exists anywhere that did not exist before. Every effect below is the SAME pre-existing `/data` Job
  progress panel, `/scanner-runs` table, and `/evidence`/`/research/factor-lab` drawdown panels now
  resolving their already-rendered fields differently over time.

---

## What Old Behavior Changed

- **Historical-day backfill's overall job status** (`/data`, Backfill snapshots job kind, target date
  earlier than the latest cached membership-timeline date): previously, even after iter-48's fix to the
  first finalize-tail step, the job as a whole could still run 20+ minutes past the advertised window
  because two OTHER pre-existing steps (`forward_aggregates_warm`, `drawdown_expectations_warm`) were
  themselves unbounded — one measured as high as 1,334s (22m14s) alone in a prior sample, and the other
  never even completed on one prior run. The job-status badge (`data-testid="job-status"`) now reliably
  leaves the spinning "running" state and settles to a real terminal label (`ok` / `no new snapshots` /
  `partial` / `failed at backfill` / `failed`) within ~17–17.5 minutes across all 3 of this iteration's
  live proofs.
- **Newly-disclosed caveat — a brief backend health blip, not caused by this iteration's own fix.** 2 of
  the 3 live runs each logged exactly one ~10-second `GET /api/health` timeout, occurring early in the SAME
  run (roughly 42–44 seconds in), at the boundary between the backfill stage and the
  `coverage_membership_timeline_refresh` step — BEFORE either of the two phases this iteration bounds even
  begins. This is a newly-surfaced, disclosed-but-not-fixed gap (explicitly out of this iteration's scope
  per `docs/goal.md`'s own carried item). Practically: an operator watching the "Ready" badge in the page
  header at exactly the wrong moment, early in a historical-gap backfill, could see it flicker briefly
  before recovering on its own; it was not observed to stay down.
- **`/backtest` and `/evidence`/`/research/factor-lab`'s drawdown-expectations and forward-aggregate
  reads**: no visible change in the numbers shown — this is a server-side calculation-speed change only
  (a ratio computed once and reused across accumulators instead of recomputed per accumulator; a
  column-projected database read replacing a full-row read for the ingest warm step). Both changes are
  proven byte-identical against a pinned pre-fix reference on every configured horizon and every ledger
  claim.

---

## Not Visible Yet

- The new **per-horizon** (`forward_aggregates_warm`) and **per-claim** (`drawdown_expectations_warm`)
  sub-phase timing breakdown exists only in the backend's server log (`logs/backend.log`, `"J-05
  finalize-tail sub-phase timing"` lines naming the specific horizon or claim that took the longest). There
  is no UI panel showing this — the `/data` page's existing "Stage timings" block (`data-testid=
  "stage-timings"`) only ever showed the fetch/backfill stages, and this iteration did not extend it to the
  finalize-tail phases; an operator needs log access to see which specific horizon or claim was slowest.
- The new single-flight lock fall-through log line (added to make future lock contention observable) is
  likewise server-log-only, with no UI counterpart.
- The newly-disclosed ~10-second health-poll gap has **no UI indicator of its own** — no "still starting
  up" or degraded-state badge appears during that window; it is invisible unless a human happens to check
  `/api/health` (or watch the Ready badge) at exactly the wrong second.
- The remaining slowest research claim this iteration deliberately did NOT speed up
  (`_combination_observations`, ~252–254s live — now the single most expensive item in the finalize tail)
  has no per-item progress indicator anywhere in the UI, same as every other sub-phase — only the whole-job
  status and the server log show anything about it.
