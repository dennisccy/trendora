# goal-ops-hardening-iter-61 Execution Plan

## Context / Goal Alignment
This iteration is a targeted repair + evidence-honesty pass, not new capability work. It
directly advances `docs/goal.md`'s J-05 ("Aggregates are precomputed at ingest, never on
the fly") and J-07 ("Heavy aggregates never take the service down") by (a) fixing a
concrete stale-read defect the iter-60 evaluator independently reproduced from
sqlite/screenshots, and (b) replacing an unreconciled prose claim with a raw, reconciled
measurement. No drift from the project goal: it touches only already-registered Data
Contract values (Coverage payload; Regime-Lab degrade-state fields) at their existing
producer/endpoint (`app.engine.data_manager` / `GET /api/data`), introduces no new page,
nav entry, or contract value, and explicitly restates the owner-only J-07 ceiling question
rather than deciding it. Builds directly on iter-60's work (the `replay-lane.sh`
`TARGET_JOURNEYS` routing fix and the Regime-Lab prologue isolate-and-continue /
`sample-link.tsx` `unavailable` prop) without duplicating it — this iteration only needs to
*verify* the replay-routing fix took effect live and *capture evidence* for the already-shipped
indicator, per the spec's binding order.

**Process note for the developer:** confirm current git state of
`apps/backend/app/engine/data_manager.py`, `research.py`, `test_regime_lab.py`,
`_labs.tsx`, and `lib/api.ts` before starting (`git status` / `git diff`) — this session's
long-running loop may have left prior-iteration edits committed or still pending; do not
assume a clean baseline matching the iter-60 handoff without checking.

## What to Build
- **Root-cause and fix the `/data` coverage staleness defect.** After a real ingest's
  finalize hook persists a fresh `coverage_snapshot` row (`compute_coverage` /
  `_upsert_coverage_snapshot` in `app.engine.data_manager`), the same never-restarted
  process must keep serving that row's exact `snapshot_count`/`gap_count` via
  `coverage_from_storage` / `GET /api/data` — including after an intervening
  `_membership_dataset_version` bump caused by an unrelated request-path event (e.g. a
  `/backtest` view creating a new `ScannerRun`). Diagnose first: either
  `coverage_from_storage`'s `asof_key`-only lookup is returning a superseded row instead of
  the most-recent one for that key (backend), or `/data`'s post-job-completion / periodic
  refetch is discarding a fresher response (frontend, `apps/frontend/app/data/page.tsx` /
  `lib/api.ts`). Fix ONLY the actual source — do not patch both speculatively.
- **Regression test** pinning the fix (TC-1/TC-2): ingest → fresh `coverage_snapshot`
  persisted → an unrelated request-path `ScannerRun` creation bumps
  `_membership_dataset_version` → `/data` still serves the freshest row's counts, never an
  older superseded payload.
- **Re-measure and rewrite J-07 step 2** (health responsiveness during a real 18-23 minute
  heavy ingest) from a raw `GET /api/health` once-per-second poll log. Reconcile the log's
  line count against the process's own `heavy-warm window OPEN`/`CLOSED` markers (reuse the
  reconciliation pattern from
  `runs/goal-ops-hardening-iter-59/evidence-drill/reconcile_drill.py` — do not write a new
  one). Name every non-200 response individually (if any) and the single slowest answered
  latency with its timestamp. Append the dated section to `reports/perf-budgets.md` under
  the owner-amended ≤2s bounded-background-compute-window ceiling (steady-state ≤0.1s is
  unchanged and out of scope here).
- **Capture evidence for the already-shipped "Unavailable" sample-link indicator**
  (`components/sample-link.tsx`, `data-testid="sample-link-unavailable"`) on the Regime Lab
  page: relaunch the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed
  (throwaway/relaunched dev process), load Regime Lab for a degraded cohort with a nonzero
  real observation count, capture and OPEN (not just hash) the screenshot to confirm the
  AlertTriangle + "Unavailable" element with no active drill-down link, then restore the
  backend to its normal unarmed launch for the rest of the iteration.
- **Confirm the replay-lane routing fix is live** (TC-3): this executor starts fresh,
  sourcing `replay-lane.sh` as iter-60 already fixed it — read the engine's own
  "Regression (deterministic replay):" log line and confirm it lists both J-05 and J-07
  among the replayed journeys. This is a verification task, not a code change (iter-60's fix
  could not self-verify in the run that edited it; this run can).
- **Full regression:** J-01, J-03, J-04, J-06, J-08, J-09 must all report PASS via
  deterministic replay + LLM fallback, no selector-drift failure (TC-7).
- **Walkthrough:** record J-05 and J-07 via `demo.sh ops-hardening --session-live` at full
  depth, covering both journeys' `[NEW]`-flagged acceptance clauses (TC-6).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-61-dev.md`.

### Explicitly out of scope (carry forward, do not touch even if time remains)
- Deciding the J-07 owner question (does the ≤2s ceiling apply to an 18-23 min job, or only
  the ~30s window it was written for) — restate it verbatim in the handoff's open-questions
  section; only the evaluator/owner resolves it.
- The long-carried backlog items (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n,
  iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi,
  iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k) and the Regime Lab
  UI/feature backlog (iter-33/g).
- Moving heavy Regime Lab compute into its own process.
- Re-measuring J-07 step 3 (VmPeak margin) or J-05 step 3 (cold-restart coverage) — both
  stand on prior binding evidence.
- Any new page, nav entry, or Data Contract value.

## Agents Required
- developer: yes -- root-cause and fix the coverage staleness defect (backend and/or
  frontend depending on diagnosis), write the regression test, re-run and reconcile the
  J-07 health-poll drill, capture the fault-injected Regime-Lab screenshot, verify the
  replay-lane routing live, write the dev handoff.
- backend-data: yes -- primary suspect surface (`app.engine.data_manager`'s
  `coverage_from_storage` / `_upsert_coverage_snapshot`), the regression test, and the
  health-poll reconciliation drill against a real heavy ingest.
- frontend-ux: yes (conditional on diagnosis) -- only if the staleness traces to `/data`'s
  client-side refetch/render path (`app/data/page.tsx`, `lib/api.ts`); required regardless
  for the Regime Lab evidence-capture step (armed-fault screenshot of the existing
  `sample-link.tsx` indicator — no new frontend code expected there, capture only).

## Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- root-cause fix in the stale-row resolution
  path (`coverage_from_storage` and/or `_upsert_coverage_snapshot`'s `asof_key` lookup) so
  the freshest `coverage_snapshot` row always wins for a given `asof_key`.
- `apps/backend/tests/test_data_manager.py` (or the existing coverage/dataset-version test
  file for this module) -- new fixture-backed regression test per TC-1/TC-2; existing
  coverage/dataset-version tests must still pass with no weakened assertion.
- `apps/frontend/app/data/page.tsx`, `apps/frontend/lib/api.ts` -- ONLY if diagnosis
  attributes the staleness to the client refetch/render path instead of the backend.
- `reports/perf-budgets.md` -- append-only: new dated section for the reconciled J-07
  step-2 health-poll measurement (≤2s BCW ceiling, per the 2026-07-31 owner amendment).
- Evidence artifacts under this iteration's evidence directory (raw `GET /api/health`
  poll log/CSV with `wc -l` reconciliation notes; opened Regime-Lab "Unavailable"
  screenshot; J-05 `/data` before/after screenshots showing the corrected counts).
- `docs/handoffs/goal-ops-hardening-iter-61-dev.md` -- new dev handoff, including the
  verbatim-restated owner question on J-07's ceiling scope.
- No new files expected in `components/`, `app/research/`, or `scripts/automation/lib/` —
  `sample-link.tsx` and `replay-lane.sh` are read/verified this iteration, not modified
  (both already fixed in iter-60 per its dev handoff).

## UI Evolution
- New user-facing capability: none — this iteration repairs an already-shipped display
  path (`/data`'s coverage counts) and captures missing evidence for already-shipped code
  (the Regime-Lab "Unavailable" indicator).
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — same `/data` page, same Regime Lab page; only the
  served/rendered values become current instead of stale.
- Navigation changes: none.
- Product-visible delta: a user who runs a backfill and stays on `/data` now sees the
  Snapshot Dates / Backfill Gaps counts update to match the just-finished job instead of a
  stale pre-job pair persisting for tens of minutes; a degraded Regime-Lab cell's
  "Unavailable" indicator (already shipped) now has confirmed visual evidence.

## Visual Requirements
- Component patterns: none new — reuse the existing `/data` Coverage payload panel and the
  existing `SampleLink` component's `unavailable` branch (AlertTriangle icon + "Unavailable"
  text, `text-text-faint`) exactly as iter-60 shipped it.
- Layout: unchanged on both pages.
- Key visual effects: none new; do not introduce styling changes while capturing evidence.
- States to handle: (1) `/data` immediately after a completed ingest in the same
  never-restarted process — must show the fresh counts; (2) `/data` after an intervening
  unrelated dataset-version bump — must still show the fresh counts, not stale ones; (3)
  Regime Lab under armed fault injection for a degraded cohort — the "Unavailable" state,
  visibly distinct from a genuine low-sample `n=...` chip.

## Key Test Scenarios
- TC-1: ingest finalize persists `coverage_snapshot(N, M)` → any later `/data` load in the
  same process renders exactly N/M, cross-checked directly against sqlite.
- TC-2: an unrelated request-path `ScannerRun` creation bumps
  `_membership_dataset_version` after the fresh row was written → `/data` still serves that
  same freshest row's N/M, never an older superseded payload.
- TC-3: the engine's "Regression (deterministic replay):" log line includes both J-05 and
  J-07 among the journeys actually replayed this run.
- TC-4: backend relaunched with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed →
  Regime Lab for a degraded cohort with nonzero real observations → opened screenshot shows
  `data-testid="sample-link-unavailable"` (AlertTriangle + "Unavailable"), no active
  drill-down link.
- TC-5: a real 18-23 minute ingest, `GET /api/health` polled once per second throughout →
  raw poll log's line count reconciles exactly against the sum of every reported segment,
  bounded by the process's own `heavy-warm window OPEN`/`CLOSED` markers; every non-200 (if
  any) listed individually; the single slowest latency named with its timestamp.
- TC-6: `demo.sh ops-hardening --session-live` at full depth produces a walkthrough
  recording on disk covering J-05's and J-07's `[NEW]`-flagged acceptance clauses.
- TC-7: full-regression replay of J-01/J-03/J-04/J-06/J-08/J-09 — all six PASS, no
  selector-drift failure.
- Anti-goal checks: AG-3 (displayed numbers must match the engine's computation for the
  same as-of, not just render) and AG-8 (no unbounded whole-table load introduced by the
  fix, graceful degrade preserved) apply directly to this iteration's surface.
