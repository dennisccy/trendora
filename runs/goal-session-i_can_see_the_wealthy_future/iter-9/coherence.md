**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-9 (Backtest / Time-Machine workspace + per-date forward-test scorecard, J-14)

Session: `i_can_see_the_wealthy_future` · Iteration index: 9 · Snapshot SHA: `ea28a0e` (WIP-on `acc00d5`, iter-8)
Audited: `git diff ea28a0ef101fc690d9561084f85bdf51153fccc7` + `git status --short`.

## TL;DR

No objective Data-Contract (Part A) or Information-Architecture (Part B) violation exists, because **this
iteration's diff contains no application source code at all** — there is nothing for a value to be
recomputed in, and no new page/route for the nav to lose. The only tracked changes are an **additive,
internally-coherent, single-sourced** blueprint edit and the required `blueprint.reapproval-requested`
marker. → **COHERENCE-PASS.**

**Loud advisory (not a coherence FAIL — the goal-evaluator must act on it):** the blueprint is currently
**ahead of the code**. The contract now advertises a `/backtest` route, a "Backtest" sidebar section, and a
`compute_run_scorecard` → `GET /api/backtest` Data-Contract value, **none of which exist in the working
tree**. The iteration is at `status.json: current_step="starting"`, `changed_files=[]`, no dev handoff. Do
**not** read this PASS as "J-14 was built coherently" — it means "nothing was built yet, and what the
decomposer wrote (the blueprint deltas) is coherent." Whether J-14 was actually implemented is the
goal-evaluator's call on QA evidence (which is absent).

## What this iteration actually changed (the diff)

| Change | Kind | Coherence-relevant? |
|---|---|---|
| `runs/.../state/blueprint.md` | +10 lines: Backtest IA-skeleton row, feature-home table row (J-14), "Per-date forward-test scorecard" Data-Contract row, iter-9 serving-model note | Yes — audited below (Part A/B) |
| `runs/.../state/blueprint.reapproval-requested` | new marker, one-line reason for the `/backtest` nav-skeleton change | Yes — required for a nav change; present ✓ |
| `docs/phases/goal-...-iter-9.md` | the iteration spec | No (planning doc) |
| `telemetry.jsonl`, `trace/.next-step`, `trace/trace.jsonl`, `runs/...iter-9/snapshot-sha`, `runs/...iter-9/status.json` | pipeline metadata | No |

Verified absent (would carry the J-14 implementation; none exist): `apps/backend/app/api/backtest.py`,
`apps/frontend/app/backtest/page.tsx`, `apps/backend/tests/test_backtest*.py`,
`forward_testing.compute_run_scorecard` / `backfill_run_forward_returns` / `_insert_run_forward_returns`,
a `/backtest` entry in `apps/frontend/components/sidebar.tsx`, `fetchBacktest` in `apps/frontend/lib/api.ts`.
`git status --short apps/` is empty; `git stash list` empty; single worktree at `acc00d5`. The implementation
is genuinely not present (not stashed, not in another worktree).

## Part A — Data Contract (objective → FAIL). Result: PASS

- **No new code path computes a registered value.** The diff adds zero functions/endpoints, so no
  duplicate `sharpe`/`cagr`/`return`/score computation and no non-canonical fetch can have been
  introduced. Nothing to trace to a `file:line`.
- **The one new contract row is internally coherent and single-sourced.** The blueprint registers
  **Per-date forward-test scorecard** with exactly ONE computing module
  (`app.engine.forward_testing:compute_run_scorecard`) and ONE serving endpoint (`GET /api/backtest`),
  and explicitly states it **READS the same stored `forward_returns` rows that `/api/system-health`
  aggregates** ("one source, two read paths — never two computations") and reads stored
  `scanner_results` bucket/setup/sector/rank **verbatim** (no re-bucketing/re-scoring). The `/backtest`
  page's as-of scan summary is contracted to **reuse the existing canonical endpoints** (`/api/dashboard`,
  `/api/sectors`, `/api/themes`, `/api/stocks` with `?as_of=`) — no second source for
  regime/sector/theme/stock. This is a textbook single-source extension, not a synonym/re-derivation of an
  existing value. → No Part A violation; no "unregistered value" WARN (it *is* registered).

## Part B — Information Architecture (objective → FAIL). Result: PASS

- **No new page/route/feature in the diff**, so the Part B FAIL conditions (hidden feature / >2-click /
  duplicate home / parallel shell) cannot be triggered — they require code that exists. The current
  `sidebar.tsx` (inspected: Dashboard, Stocks, Themes, Sectors, Scanner Runs, System Health, Watchlist)
  has **no** `/backtest` link, but there is also **no `/backtest` page** — so this is "feature not built,"
  not "feature built but hidden." Not a Part B violation.
- **The blueprint's IA edit is coherent and the nav-skeleton change was handled correctly.** Backtest is
  added as a single top-level section with a canonical home (`/backtest`, ≤2 clicks), no existing home is
  moved, Stock/Run Detail stay row-reached, and `blueprint.reapproval-requested` was written with a
  one-line reason — exactly the protocol for a nav-skeleton change. → No Part B violation.

## Part C — Advisory (WARN only; does not block)

1. **[HIGH-VISIBILITY] Implementation absent — blueprint precedes code.** The contract advertises J-14
   surfaces/values that have no implementing code yet (enumerated in TL;DR + "What changed"). This is a
   *completeness / pipeline-state* signal for the goal-evaluator — **not** a coherence drift — so it is
   advisory here. If a later step does build J-14, the changes must be re-audited; if it does not, the
   evaluator should treat J-14 as not-achieved on absent QA evidence (the spec's own NOTES anticipate a
   browser-qa SKIP and say to reconcile from on-disk PNGs + unit/API proofs + source reads — but none of
   those artifacts exist yet either).

2. **Coherence checklist to apply when the J-14 code lands** (pre-empting the real risks — these become the
   next coherence pass's objective checks, all already promised by the blueprint/spec):
   - **Part B nav path:** `apps/frontend/components/sidebar.tsx` must gain `{ href: "/backtest", label:
     "Backtest" }` (placed after Scanner Runs / before System Health) so `/backtest` is reachable in 1
     click — otherwise it is a genuine "hidden feature" FAIL.
   - **Part A no-recompute (the keystone):** `GET /api/backtest` / `compute_run_scorecard` must serve from
     the stored `forward_returns` + stored `scanner_results` and recompute **no** score/bucket/return. The
     forward-return INSERT must be the **one** shared helper factored out of the iter-6 `_backfill`
     per-run loop (no second forward-return formula). Confirm via the spec's patch-to-raise seam test, not
     value-equality.
   - **Part A single-source on the scan summary:** the `/backtest` page must call the **existing**
     `fetchDashboard/fetchSectors/fetchThemes/fetchStocks` with `?as_of=D` — it must NOT introduce a
     second endpoint or client recomputation for regime/sector/theme/stock values.
   - **Snapshots-immutable:** `backfill_run_forward_returns` must be INSERT-only into the existing
     append-only `forward_returns` table; `models.py` unchanged; no UPDATE of any `scanner_runs` /
     `scanner_results` / `*_scores` row.

## Notes on scope / no-op handling

Per the agent instructions, the coherence gate FAILs only on objective Part A / Part B code-drift, and "when
in doubt, choose WARN." Here there is no doubt and nothing even WARN-worthy in the *coherence* sense: the
blueprint deltas are additive and single-sourced, and there is no source diff to drift. The substantive
issue (no implementation) is explicitly outside this gate's mandate (it is the goal-evaluator's
done/stalled judgment) and is surfaced above as a high-visibility advisory rather than suppressed. Verdict
stands: **COHERENCE-PASS**.
