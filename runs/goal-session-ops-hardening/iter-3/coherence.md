# Iteration 3 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only correctness fix, confirmed by both the diff and the ui-impact-analyst's surface map
("Frontend surfaces changed: 0 pages/components had code changes... Navigation changes: no"). Files
touched: `apps/backend/app/engine/data_manager.py`, `apps/backend/tests/test_data_manager.py`,
`README.md` (documentation catch-up only), `reports/perf-budgets.md` (measurement artifact),
`runs/goal-session-ops-hardening/state/blueprint.md` (the contract update itself). No new page,
route, component, or displayed value.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | OK | `apps/backend/app/engine/data_manager.py:3810-3811` — the new `fetch`/`expand` finalize branch calls the pre-existing canonical `refresh_coverage_snapshot(agg_session, cfg)` (same function `backfill`/`both`/`rebuild` and the boot warm-up thread already call); zero second derivation |
| Coverage payload — new gate function | OK (not a computation) | `apps/backend/app/engine/data_manager.py:1060-1069` (`_coverage_snapshot_is_current`) — a boolean freshness check (one row lookup + the same cheap `_resolve_coverage_asof` call `refresh_coverage_snapshot` itself needs); grepped confirmed it never calls `_compute_coverage_uncached` (verified: only 1 call site of `_compute_coverage_uncached` in the whole module outside its own definition/docstrings, at `data_manager.py:751` inside `_compute_coverage_uncached`'s own caching wrapper — the gate function does not appear in that call graph) |
| Coverage payload — stale-row reclaim (B2) | OK | `apps/backend/app/engine/data_manager.py:86` (`_upsert_coverage_snapshot`) — widened from a per-`asof_key` `DELETE` to one bulk `DELETE ... WHERE dataset_version != :current` across all `asof_key`s; same table, same shape, no new derivation; test `test_stale_dataset_version_rows_pruned_via_one_bulk_delete` asserts exactly 1 DELETE statement |
| Backfill run-summary contract (`aggregates_refreshed` nullability) | OK | `apps/backend/app/engine/data_manager.py:3790-3811` — new `elif` branch deliberately never sets `prog.aggregates_refreshed`; the field's existing backfill/both/rebuild-only nullability is untouched, matching the spec's explicit "Out of scope" item and the blueprint's Backfill run-summary contract row |
| New displayed value | N/A | None introduced — spec's "Data-contract additions" and "New information displayed" sections both state "None"; confirmed no new field/panel in the diff or ui-surface-map |

Traced both ends for the one row this iteration touches: the blueprint's Coverage payload row names
`app.engine.data_manager` / `_compute_coverage_uncached` / `GET /api/data` as canonical, and the
diff's only new write path (`_run_job`'s new `elif`) reaches the value exclusively through
`refresh_coverage_snapshot` → `refresh_coverage_snapshot_for` → `_compute_coverage_uncached` — the
same chain the pre-existing backfill/rebuild branch and the boot warm-up thread already use. No
second computing module, no second serving endpoint, no client-side recomputation (there is no
frontend change at all).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` (Data Manager) | OK — no change | No frontend file in the diff; blueprint's IA table already lists `/data` as J-05's canonical home. Iteration spec's "Blueprint conformance" and "UI surface changes: None" both confirm no nav-skeleton change; no `blueprint.reapproval-requested` file was written (confirmed absent) |

No new page/route/feature was introduced this iteration, so there is nothing new to check for
reachability, duplicate homes, or a parallel shell. The one behavior change (coverage freshness after
`fetch`/`expand`) surfaces through the pre-existing `CoveragePanel` on the pre-existing `/data` page,
fed by the pre-existing `GET /api/data` endpoint — confirmed unchanged by the ui-surface-map's
"Modified components: 0."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint update accompanying this iteration is internally consistent: the Coverage payload
  row's `[TARGET, iter-3 building]` retag describes exactly the widened trigger + bulk-delete
  reclaim implemented in the diff, and the three tags it removes (`aggregates_refreshed`, the
  market-phase warm-trigger row, the membership-timeline/research-hot-key row) correctly cite
  iter-2 evaluator-confirmed builds unaffected by this iteration's change — verified against
  `git diff aa3374828e8bb4f1499566c7b2b7665bcc2de648 -- runs/goal-session-ops-hardening/state/blueprint.md`.
- The README's "Data Manager" and "Fast-ready boot" bullets pick up documentation for the
  ingest-time coverage snapshot and the "Refreshed: ..." line — both actually shipped in iter-2, per
  the ui-surface-map's own "Unchanged — regression check" rows for that line. This is documentation
  catching up one iteration late, not a new or duplicated value; no coherence rule is implicated.
- No other formatting/labeling drift observed — this iteration touches no UI-rendered text.
