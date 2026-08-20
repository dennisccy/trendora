# Incident record — iter-5 execution checkpoint superseded by a goal amendment

**Date:** 2026-08-20 · **Session:** market-compass · **Branch:** `goal/market-compass` · **Owner-directed**

## What happened

Iteration 5's live J-05/J-06 drill executed its own spec step (i) — remove + backfill of
**2026-08-11 and 2026-08-12** — believing those dates were seed-safe. They were not. The committed
seed's window ends **2026-07-01** (`apps/backend/data/seed/meta.json`), so those two trading days
came from earlier live fetches and backfill had nothing local to read back.

State verified directly against the database after the drill (read-only):

- `daily_prices` maximum date is now **2026-08-10** (NVDA / AAPL / GRMN spot-checked)
- `scanner_runs` maximum `asof_date` is now **2026-08-10** — the 08-11 and 08-12 runs are gone
- `next_session_manifests` still holds **24 rows reaching as_of 2026-08-12**, export files intact —
  **AG-12 held at the storage layer**: the manifests survived, their source data did not
- `GET /api/compass?as_of=2026-08-12` now returns HTTP 400; J-01 / J-02 / J-03 fail a live replay

No live fetch was performed in response. The latest `data_provider_runs` rows are all
`provider='seed'` (offline ingest).

## Owner response

`docs/goal.md` was amended on this branch (commit-pending at the time of writing):

- **J-10** — bounded recovery journey for exactly 2026-08-11 and 2026-08-12
- **AG-9** — dated, single-use, self-closing exception authorizing only that recovery
- **AG-17** — repair never rewrites provenance (no retroactive `prospective_eligible` upgrade;
  damaged-DB artifacts stay unusable as prospective/OOS evidence; the incident record is preserved)
- **Constraints** — destructive-drill isolation recorded as a defect + future direction
- **Loop mechanics** — owner insert #2: J-10 jumps the queue and gates every other lane

## What was changed to reset the planning cursor

`runs/goal-session-market-compass/session.json`: **`current_iter` 5 → 6** (plus `updated_at`).
Nothing else. `last_verdict` was deliberately **left at `CONTINUE`** — that is iter-4's real
verdict; iteration 5 was never evaluated, and no verdict was fabricated for it.

**Why this mechanism:** the engine's own `step_invalidate_from decomposer` was rejected — its
ledger entry `runs/goal-session-market-compass/iter-5/.steps/decomposer.done` registers
`docs/phases/goal-market-compass-iter-5.md` as an artifact, so invalidating would have **deleted
the very spec that instructed the destructive drill**, and the re-planned iteration would have
overwritten it at the same path. Advancing the cursor is the narrowest action that returns control
to the decomposer while leaving every iter-5 artifact byte-intact.

## What is preserved (untouched by this change)

- `docs/phases/goal-market-compass-iter-5.md` — the spec that instructed the drill
- `docs/handoffs/goal-market-compass-iter-5-dev.md` — the dev handoff and its incident evidence
- `runs/goal-market-compass-iter-5/status.json` — `current_step: dev_complete`, `next_action:
  review`, with all four recorded blockers including the deletion and the concurrent-sub-agent
  process finding
- `runs/goal-session-market-compass/iter-5/` — step ledger, goal slices, review packet, snapshot SHA
- `runs/goal-session-market-compass/state/assumptions.md` — the developer's own iter-5 entry
- `reports/phase-goal-market-compass-iter-5-*` and `reports/qa/goal-market-compass-iter-5-evidence/`
- Commits `5f7cc04c` / `9dd91338` (iters 3 and 4) and their showcase commits — untouched

**Semantics: the old continuation point is obsolete; iteration 5 still happened.** Iteration 5 has
no `eval.md` and never will — it was superseded before evaluation, not evaluated and dismissed.

## Next action

`/goal-resume market-compass` starts **iteration 6** with a fresh decomposer pass against the
amended `docs/goal.md`. No lane may run against the damaged database until J-10's post-recovery
verification passes.
