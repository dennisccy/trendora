# Iteration 35 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

One new value is registered this iteration: the **live-vs-seed drift report** (blueprint.md Data
Contract table, "building iter-35 — J-21/B-304" row; iter-35 clarification paragraph appended at the
end of the file).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Live-vs-seed drift report | OK | Computed once: `apps/backend/app/engine/drift.py:80` `build_drift_report` — a PURE, side-effect-free comparator; called from exactly one production call site, `apps/backend/app/engine/data_manager.py:2339` inside `_check_drift`, which is itself called from exactly one place, `data_manager.py:3177` inside `_run_job`, guarded to run only on a completed (non-`resumable`) fetch (`data_manager.py:3176 if overlap_sink is not None and prog.status != "resumable"`). Confirmed via `grep -n "_check_drift("` and `grep -n "build_drift_report"` — no second definition, no second call site anywhere in `apps/`. |
| Live-vs-seed drift report — serving | OK | Single reader `apps/backend/app/engine/drift.py:133 read_drift_report()`, called verbatim by both consumers and nowhere else: `apps/backend/app/engine/readiness.py:323` (`compute_preflight`'s new `drift` component) and `apps/backend/app/api/data.py:145` (`"drift": read_drift_report()` on `GET /api/data`). `grep -rn "read_drift_report"` across `apps/` shows only these two production call sites (all other hits are tests/docstrings). Neither caller re-parses the artifact or recomputes the comparison — `compute_preflight` only maps `status` → `ok`/detail text (the same pattern already used for `servability`/`freshness`/`integrity`). |
| Live-vs-seed drift report — frontend display | OK | `apps/frontend/app/data/page.tsx:804 DriftReportPanel` renders `state.data.drift`, and `state.data` is populated from the single existing `GET /api/data` call (`apps/frontend/lib/api.ts:2492`, `fetchDataCoverage`'s sibling overview fetch) — confirmed no new frontend fetch function was added for drift (`grep -n "DriftReportPanel"` shows one definition + one call site; the component branches on `drift.status` and reformats dates/counts for display only — no client-side recomputation of the comparison). The cross-cutting `PreflightBanner` (`apps/frontend/components/preflight-banner.tsx`) is untouched by this diff (confirmed: `git diff <snapshot> -- .../preflight-banner.tsx` is empty) and needed no change — it already renders `preflight.reasons` generically via `.map()` (lines 80-85), so the new "drift" reason string flows through the existing single `/api/health` poll (`useReadiness()`) with zero new code. |
| Config plumbing (`DriftCfg`/`DataQualityCfg`, `ReadinessCfg.severity["drift"]`) | OK | One new config block (`apps/backend/app/config.py:101-115` `DataQualityCfg`/`DriftCfg`), one `^data_quality:` key in `config.yaml:1120` (confirmed no duplicate top-level key via grep), and `ReadinessCfg._validate`'s required-component set extended consistently (`config.py:557`) with matching test-fixture updates across `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` — all add the same `"drift": "degraded"` entry, no divergent copies. |

No duplicate computation, no non-canonical source, no unregistered new value. The value is
conceptually distinct from every other registered Data Contract row (evidence status, preflight
verdict, capacity snapshot, etc.) — it is a new integrity report the preflight verdict *composes*, not
a re-derivation of any existing value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` drift report section | OK | No new route. Additive card on the EXISTING `/data` page (J-13's already-registered Data Manager home per blueprint.md IA homes table). `git diff <snapshot> -- apps/frontend/components/sidebar.tsx apps/frontend/app/layout.tsx` is empty, and `git status --porcelain apps/frontend/app/` shows no new route directories — confirmed no nav-skeleton change. |
| Preflight banner drift reason | OK | Cross-cutting chrome, mounted once in `app/layout.tsx` since iter-33; unchanged this iteration (diff empty). Reachable identically to every other page (0 additional clicks — it's already on every page). |

Blueprint's own "Blueprint conformance" claim in `docs/phases/goal-mcp-loop-iter-35.md` ("no
nav-skeleton change, no reapproval note filed") is verified true: no
`runs/goal-session-mcp-loop/state/blueprint.reapproval-requested` file was created (not present in
`git status` untracked list), and the blueprint.md IA homes table already carries the new J-21 row
(`/data` + cross-cutting readiness/preflight) consistent with what was actually built.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration is unusually disciplined about single-sourcing: one comparator, one artifact
  writer, one reader shared by both consumers, zero new endpoints, zero new pages, zero nav changes,
  and the blueprint file itself was updated in the same commit-set with a matching Data Contract row
  and IA homes-table row before I read it. No inconsistent labels, no divergent formatting, no
  unregistered value found.
