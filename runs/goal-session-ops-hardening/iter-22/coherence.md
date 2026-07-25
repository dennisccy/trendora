# Iteration 22 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-22
**Date:** 2026-07-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (context for the checks below)

Confirmed via `git diff 583e318838e7d028b1d3e67c902b8608bd47a6c5 --stat` (full tree, no path exclusions):
exactly 6 files changed, zero of them under `apps/backend/` or `apps/frontend/`:

- `docs/improvement-backlog.md` (+13/-0) — new backlog card B-1107, status `PROPOSED`, not built.
- `reports/perf-budgets.md` (+225/-8) — new "Iteration 22" section + a same-day "Revision 1" edit to the
  existing "OWNER BUDGET AMENDMENT" section.
- `runs/goal-session-ops-hardening/state/blueprint.md` (+4/-2) — one new dated comment-block paragraph +
  one appended sentence on an existing Data Contract row's Notes cell.
- 3 harness-bookkeeping files (`telemetry.jsonl`, `trace/.next-step`, `trace/trace.jsonl`) — outside
  review scope.

This matches the iter spec's own "zero product source changes" framing and the dev handoff's stated
`git status`/`git diff` verification (both empty for `apps/backend` and `apps/frontend`), independently
reproduced here.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Page performance budgets (measurement artifact) | OK | `reports/perf-budgets.md:3525-3706` ("## Iteration 22" section) appends to the SAME already-registered artifact — `blueprint.md:335` Data Contract row lists it as "N/A — a measurement artifact, not a served runtime value," served by exactly `reports/perf-budgets.md`. No second budgets file created; no served/displayed product value touched. |
| BCW budget ceiling (`/backtest` ≤8.0s, `/api/health` ≤2.0s, window ≤90s) | OK | `reports/perf-budgets.md:3449` (ceiling text edited in place, 60s→90s) + `:3463-3495` ("Revision 1" narrative). One current authoritative ceiling; the superseded number is preserved only as dated history, matching this file's established editing pattern since iter-2. |
| Backlog card B-1107 (bound concurrent historical background computes) | OK — not a Data Contract item | `docs/improvement-backlog.md:3107,3139-3150` — the card is explicit and correct about its own non-scope: "`★ Canonical value: none — re-reads existing payloads; the cap changes scheduling only, never a served number`." Status `PROPOSED`; no code exists yet to audit. |
| `/backtest` evidence payload (`evidence_by_horizon`, `evidence_status`, `evidence_generated_at`, `evidence_asof`) / `GET /api/health` readiness | OK | Zero diff under `apps/backend/app/engine/forward_testing.py`, `apps/backend/app/engine/readiness.py`, `apps/backend/app/api/backtest.py`, `apps/backend/app/mcp/tools.py` — `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and `ensure_historical_forward_aggregates_dispatched` are byte-unchanged since iter-20/21 (binding "Do not redo," re-confirmed by this iteration's own TC-14 byte-identity spot check, `reports/perf-budgets.md:3645-3653`). |

No new function, service, module, or endpoint was added anywhere in this diff, and no new UI surface
fetches anything — trivially, neither a duplicate-computation nor a non-canonical-source violation is
possible this iteration. The only "new" content (the Iteration-22 measurement numbers and the B-1107
proposal) lands inside already-registered artifacts, not as second sources for any existing value.

## Information Architecture check

No new page, route, or feature this iteration — the iter spec's own "New user-facing capability / New
information displayed / New user actions / UI surface changes" fields all state "None," and the diff
confirms it: zero files changed under `apps/frontend/` (including `apps/frontend/components/sidebar.tsx`,
the nav component named in blueprint.md's own header). The blueprint's `## Information Architecture`
section (nav skeleton + Feature/journey-homes table, `blueprint.md:279-316`) and the canonical
module/endpoint columns of the `## Data Contract` table are byte-identical to the pre-iteration snapshot;
the only blueprint edits are the dated comment-block paragraph (intent narrative) and one Notes-cell
sentence on the pre-existing "Page performance budgets" row — neither adds, moves, renames, or removes a
nav entry or a feature's canonical home.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | N/A | `apps/frontend/components/sidebar.tsx` unchanged (zero diff under `apps/frontend/`); `blueprint.md:279-316` (IA table) unchanged |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Incidental 5-way concurrent dispatch, correctly disclosed and backlogged, not a coherence finding.**
  The developer's own discovery-phase probing (checking 5 candidate historical dates in a loop) incidentally
  triggered 5 concurrent background computes — a pre-existing, unchanged behavior of
  `ensure_historical_forward_aggregates_dispatched` since iter-20 (single-flight is keyed per
  `(asof_key, dataset_version)`, not global) — and observed `VmPeak` plateau 32 kB under the `ulimit -v` cap
  (`reports/perf-budgets.md` § "Incidental finding," `docs/handoffs/goal-ops-hardening-iter-22-dev.md` §
  "Investigation"). It was disclosed at length rather than quietly discarded, and correctly captured as a new,
  not-yet-built backlog card (B-1107) rather than an undisclosed scope expansion or a silent code change.
  It touches no computing module, endpoint, or nav surface, so it is not a Data Contract or IA violation under
  this gate — noted here only for downstream continuity.
- **Same-day budget revision creates two truthfully-scoped but differently-worded readings of one
  measurement — a scoring nuance, not a duplicate-source defect.** `reports/perf-budgets.md`'s own
  "Iteration 22" § TC-4 scores the fresh 68.79 s window measurement **FAIL** against the 60 s bound that was
  literal in the iter-22 spec's test-first contract at write time, while § "Revision 1" (same file, written
  the same day) retroactively raises that bound to 90 s and states the identical 68.79 s figure "passes with
  ~21 s margin." Both statements are individually accurate for the bound each was scored against, and the
  file maintains exactly one current authoritative ceiling (90 s, with the superseded 60 s preserved only as
  dated narrative) — there is no second budgets artifact and no scattered source. This is a pass/fail
  sequencing question for the goal-evaluator to weigh, outside this gate's Data Contract / Information
  Architecture rules, so it is not scored as a violation here.
