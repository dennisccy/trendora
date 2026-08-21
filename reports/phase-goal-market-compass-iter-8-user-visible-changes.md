# Phase goal-market-compass-iter-8 — User-Visible Changes

**Phase:** goal-market-compass-iter-8
**Date:** 2026-08-21
**Written by:** ui-impact-analyst

**Status:** N/A — Backend-only phase (Frontend Present: no)

No user-visible changes. All changes are internal backend implementation.

---

## Why this classification

This iteration (J-10 recovery redesign: precommitted path-agreement + stable multiplicative bridge,
per symbol) changed exactly four source files, all backend, per
`docs/handoffs/goal-market-compass-iter-8-dev.md`'s "Files Changed" list (corroborated by that
handoff's own `git status --short` confirmation: "the diff is scoped to exactly the files above"):

| File | diff-to-ui-impact classification | Reason |
|---|---|---|
| `apps/backend/app/engine/j10_recovery.py` | backend-internal | Recovery/engine orchestration logic under `app/engine/`, invoked only by a standalone one-time incident-recovery script — not a route handler, not called from any API request path. |
| `apps/backend/app/data_providers/yahoo_provider.py` | backend-internal | Docstring-only change this iteration (notes `get_adjusted_close`/`_parse_adjusted_close` are no longer used by the live gate). No route exposes this provider client. |
| `apps/backend/tests/test_j10_recovery.py` | backend-internal | Test file. |
| `apps/backend/tests/test_provider_clients.py` | backend-internal | Test file. |

Plus four non-code artifacts: `runs/goal-session-market-compass/state/assumptions.md` (2 new dated
entries), `runs/goal-market-compass-iter-8/j10-convention-evidence.json` (new evidence artifact, not
served by any endpoint), `docs/handoffs/goal-market-compass-iter-8-dev.md` (this iteration's dev
handoff), and `runs/goal-market-compass-iter-8/status.json` (process state). None are application
code and none are frontend-direct or backend-api by the diff-to-ui-impact skill's rules.

No file under `apps/frontend/` was touched, and no file under `apps/backend/app/api/` (route
handlers) was touched. This matches:
- `docs/phases/goal-market-compass-iter-8.md`'s own metadata: `**Frontend Present:** no`
- That same spec's `### Frontend` section: "None — J-10 has no UI surface (goal.md: 'Walkthrough:
  waived — data-layer repair with no UI surface change of its own')"
- `### New user-facing capability` / `### New information displayed` / `### New user actions` /
  `### UI surface changes` sections: all "None this iteration"
- The dev handoff's own pre-handoff checklist: "Frontend was not started (not needed —
  `Frontend Present: no`...)"

`runs/goal-market-compass-iter-8/plan.md` (the path this report's dispatch named as the primary
source for this check) does not exist on disk. Per this agent's standing instructions and the
precedent set by `reports/phase-goal-market-compass-iter-7-user-visible-changes.md` (the same J-10
feature, one iteration earlier, which hit an identical situation), the phase spec's own Goal Mode
Metadata block is the authoritative substitute when plan.md is unavailable.

**Note on a dispatch discrepancy:** the coordinator message that dispatched this report stated
"Frontend Present: yes" and a frontend URL (`http://localhost:3255`). That line reflects the overall
Trendora project (which does have a frontend, per `.claude/project-template.md`), not this specific
iteration's diff. It contradicts the phase-spec metadata above, the dev handoff (zero frontend files
touched), and the coordinator's own accompanying note, which explicitly states "The honest analysis
is almost certainly 'backend-only, no user-visible change of its own' — say so plainly... rather than
manufacturing UI surfaces or click paths." This report follows the phase spec and the coordinator's
explicit instruction, not the generic dispatch line.

## What Users Can Now Do

None. No new capability is reachable from the UI this iteration. The redesigned per-symbol
convention gate, the bridge-transform provider wrapper, and the persisted evidence artifact all run
only inside `run_gated_recovery`, invoked by a standalone recovery script — never from a request path
any page calls.

## What Changed in the Visible UI

Nothing. No frontend file was modified.

## What Old Behavior Changed

None, as a direct result of this iteration's code. No route handler, no frontend component, and no
API response schema changed. (See the incidental data-consequence note below for the one nuance worth
recording precisely.)

## Not Visible Yet

- The redesigned two-part convention gate (`check_adjustment_convention_per_symbol`,
  `_compute_symbol_verdict`) and the bridge-applying provider wrapper (`_BridgeApplyingProvider`) now
  exist in the backend, but neither has nor needs a UI surface — both run only as part of the one-time
  incident-recovery driver, not a request path any page calls.
- The persisted per-pair evidence artifact (`runs/goal-market-compass-iter-8/j10-convention-evidence.json`)
  is an internal orchestration record, never served by any endpoint or displayed to a user (the phase
  spec's own "Data-contract additions: None" confirms this).

## Pre-Existing Endpoint Behavior — Changed As An Incidental Data Consequence (context only, not a UI change this iteration made)

`GET /api/compass` is a pre-existing endpoint already consumed by the frontend's market-compass UI
journeys (J-01 et al.) — this was true before this iteration and its route file was not touched this
iteration. Its observed response for one specific date changed, as a side effect of the underlying
data now existing, not because of a code change to the endpoint or its callers:

- `GET /api/compass?as_of=2026-08-12` now returns **HTTP 200** (was 400 in iterations 6/7), per the
  dev handoff's step 5(f) direct, read-only check against a transiently started backend. This is a
  consequence of the raw-data repair (40 new `daily_prices` rows across 2026-08-11/2026-08-12 for 20
  of 587 proven-missing symbols) plus an incidental backend-boot side effect that computed
  `ScannerRun` snapshots for those two dates — **not a change this iteration made to any UI-facing
  code.**
- This does **not** mean the incident is repaired. 567 of 587 proven-missing symbols are still
  missing for those two dates, and per `docs/goal.md`'s newly-recorded J-10/J-11 responsibility
  boundary (goal.md line ~918: "587-symbol population (currently 20 restored / 567 pending)"), the
  final repaired-state J-01/J-02/J-03 replay claim belongs to a separate, not-yet-run **J-11 Stage
  G** — not to this iteration. Normal product/research lanes remain blocked after J-10 and before
  J-11 Stage G passes (goal.md line ~1270).
- The 2026-08-11 and 2026-08-12 `ScannerRun` rows created during this iteration are documented,
  temporary, recovery-era derived state — goal.md is explicit that J-11 exists specifically to clear
  and regenerate them, not that they are final snapshots a user should trust as complete.
- **No browser session was opened to observe this**, and none should be: per `docs/goal.md`'s lane
  gate, verifying any UI journey against the current, still-partially-repaired dataset is out of
  scope until J-11 Stage G passes. A replay lane that already ran against this damaged database is a
  recorded incident, quarantined at
  `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` (confirmed present on
  disk; left untouched by this report). This report does not plan or recommend browser verification
  against the current dataset.
