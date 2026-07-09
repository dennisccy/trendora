# Iteration 23 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-23
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

iter-23 is a verification-only re-run (per its own spec: "zero new feature code") that closes the
iter-22 `CLOSURE-FAIL` by re-running `browser-qa-agent` + `ux-regression-reviewer` + `phase-closure`
against the already-shipped, already-fixed J-14 build. Confirmed independently via
`git diff 7784cd3f8a1f44404f0506c327c36a8c76929fce` (tracked-file diff) and the ui-impact-analyst's
surface map: **zero backend production files and zero frontend files changed.** The only tracked
diffs are:

| File | Nature |
|---|---|
| `README.md` | Documentation prose update describing already-shipped J-14 capability (deep index lines, vendor labels, the `/data` provenance panel) — no code. |
| `apps/backend/tests/test_api_indexes.py` | Test-only change: refines an existing assertion to correctly allow the honest asymmetry between `full=true` and clamped index-series modes (a symbol whose first bar postdates an early as-of is legitimately absent from clamped mode but present in full mode). |
| `runs/goal-session-mcp-loop/journey-scripts/J-13.json` | QA golden-replay fixture: `"587 symbols"` → `"590 symbols"`, matching the additive `^SPX`/`^NDX`/`^DJI` load iter-22 already shipped. Sanctioned explicitly by this iteration's spec ("Permitted test-fixture refresh"). |
| `runs/goal-session-mcp-loop/state/blueprint.md` | The IA table's J-14 Dashboard-home label corrected from stale "major-indexes & regime card" to the live "Regime × phase cross-view card" (this coherence-auditor's own iter-22 advisory), plus an appended iter-23 clarification paragraph stating "no contract change." Route (`/`) and nav section (Dashboard) unchanged. |

No new displayed value, no new endpoint, no new page/route, and no navigation change — consistent
with the iteration spec's "Data-contract additions: None" / "Blueprint conformance: no new surfaces."

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-series vendor label + honest first-bar window (`app.engine.indexes:compute_index_series` → `GET /api/indexes`) | OK | `apps/backend/app/engine/indexes.py:84-91` — `full` is a boolean parameter on the SAME `compute_index_series` function (not a second implementation); `apps/backend/app/api/indexes.py:26-27` — exactly one `@router.get("/indexes")` definition. `test_api_indexes.py`'s edit only tightens the test's overlap-comparison to `assert set(clamped_by_sym).issubset({s["symbol"] for s in full["series"]})` and skips symbols honestly absent from clamped mode — it asserts single-compute-path behavior, it does not add one. |
| Same value, README.md description of the `/data` "Index & benchmark data provenance" panel | OK | `README.md` prose re-describes the panel registered in the iter-22 Data Contract clarification (verbatim endpoint, no new fetch path) — documentation only. |
| Universe/pool symbol count (`data_manager` coverage → `GET /api/data`) | OK | `runs/goal-session-mcp-loop/journey-scripts/J-13.json:7` — fixture text update only (587→590), matching a count already shipped in iter-22; not a new computation. |

No new value/entity is introduced this iteration (none is displayed that wasn't already registered
in the iter-22 Data Contract clarification), so Part A's "unregistered value" check does not apply.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-14 Dashboard home (`/`) | OK | `runs/goal-session-mcp-loop/state/blueprint.md:82` — label-only correction ("major-indexes & regime card" → "Regime × phase cross-view card"); route and Dashboard nav section unchanged. Confirmed the corrected name matches the actually-shipped card by cross-reading `README.md`'s own description ("a single **Regime × phase cross-view** chart..."). No sidebar/router file touched — `components/sidebar.tsx` is not in the diff. |

No new page/route/feature exists this iteration (ui-surface-map: "New pages/routes: 0",
"Navigation changes: no"), so reachability/duplicate-home/parallel-shell checks have nothing new to
evaluate.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Carried-forward WARN (not new, not worsened):** the dead-duplicate `index-regime-chart.tsx` /
  `major-indexes-card.tsx` components flagged at iter-22 remain undeleted. This iteration's spec
  explicitly defers that cleanup ("OUT OF SCOPE... a source change that would muddy this
  verification-only signal") to a dedicated tidy iteration — a reasonable call for a verification-only
  pass. Recorded here again so the next iteration that does touch frontend source picks it up.
