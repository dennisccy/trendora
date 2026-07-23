# Phase goal-ops-hardening-iter-12 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-12
**Date:** 2026-07-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration is an explicit verification-and-documentation closeout (plan.md, the phase spec, the
dev handoff, and the implementation summary all agree on this). The dev handoff's own "Files Changed" list
and a direct `git status`/`git diff --stat -- apps/backend apps/frontend` check both confirm:

- `reports/perf-budgets.md` — modified (three new sections appended; see below).
- `docs/handoffs/goal-ops-hardening-iter-12-dev.md` — new (this iteration's dev handoff).
- `reports/phase-goal-ops-hardening-iter-12-implementation-summary.md` — new (developer-authored summary).
- `runs/goal-ops-hardening-iter-12/status.json` — new (pipeline bookkeeping).

Zero of these are under `apps/frontend/` or `apps/backend/`. `git status --porcelain -- apps/backend
apps/frontend` returns empty, and `git diff --stat -- apps/backend apps/frontend` returns empty. There is no
new action a user can take that they could not take before this iteration.

---

## What Changed in the Visible UI

Nothing. Plan.md's own "UI Evolution" section states it plainly: "New user-facing capability: none. New
information displayed: none. New user actions: none. UI surface changes: none. Navigation changes: none."

`Frontend Present: yes` was set for this iteration for one reason only — to force the goal-mode harness's
browser-qa lane to actually run against already-shipped surfaces, specifically:

- **G2's controlled re-measurement**: three independent, cache-disabled, fresh-navigation real-Chrome loads
  of `/data`, each timing `GET /api/indexes?full=true` and cross-checked against `logs/backend.log` (no
  in-flight ingest job) and `logs/hwmon/hwmon.csv` (idle load1/MemAvailable) at that exact timestamp.
- **The required-still-passing replay** of J-01, J-03, J-04, and J-05 — deterministic golden replay where
  available, LLM-fallback re-verification otherwise.

None of the surfaces those two testing lanes touch (`/data`'s job form / progress panel / coverage panel,
`/scanner-runs`, the top-bar readiness badge, the preflight/crash banner) had any code change this iteration
— see the UI Surface Map companion report for the specific re-verification/measurement rows and their exact
"what to test" actions.

---

## What Old Behavior Changed

None from a user's vantage point. Every production code path a user's browser actually exercises on these
surfaces — `GET /api/health` / boot readiness (`app.engine.readiness`), the ingest finalize hooks that
populate `scanner_results` / `market_phase_cache` / the coverage payload, the job-status computation
rendered on `/data`'s job-history panel, and `compute_forward_aggregates`/`forward_aggregates_cached` itself
— was explicitly untouched this iteration. The plan's own "Do not touch" list names `app/api/health.py`,
`app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`, and `forward_testing.py` itself as
binding "do not redo" items, and the dev handoff confirms zero modification to any of them (`git diff` on
`forward_testing.py` is empty).

The only substantive work this iteration did was **reading and recording**, not changing:

- Transcribing an already-captured performance sweep from a temporary evidence file into the canonical
  `reports/perf-budgets.md` (verbatim, no editing of the numbers).
- Reading three `data_provider_runs` database rows directly (read-only) and writing a finding about them in
  the dev handoff.
- Appending a correction note to an existing audit table naming a code location that a prior audit had not
  examined — the location itself (`apps/backend/app/engine/forward_testing.py:826`) was named, not modified.

None of this is observable by a user in any running page.

---

## Not Visible Yet

- **`reports/perf-budgets.md`'s new sections** (G1 sweep transcription, G2 preparatory idle-window
  cross-read, and the TC-4 audit-correction addendum, lines ~1728–1891) are a project-internal
  measurement/documentation artifact. There is no route or page that serves this file's contents to a user
  — it exists only in the repository, exactly as it did before this iteration (as a canonical record, just
  with more content in it).
- **G2's actual three-load browser control measurement of `GET /api/indexes?full=true` has not been
  performed yet.** This developer turn completed only the preparatory idle-window log/hwmon cross-read
  (confirming no Trendora ingest job is in-flight, though the shared host itself is measurably busier than
  this file's own idle baseline right now). The three independent, cache-disabled, fresh-navigation Chrome
  loads themselves — and their resulting latency numbers — are browser-qa-agent's own pass, still to come in
  this pipeline. Until that pass runs, `/api/indexes?full=true`'s over-budget reading still has no valid
  like-for-like control on record.
- **The AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load `MemoryError`**
  remains unresolved — this iteration's `data_provider_runs` read reconfirms it as a live, reproducible
  failure on all three sampled rows (120/121/122), not a one-off, and one instance cascaded into a second
  endpoint's HTTP 500 (`GET /api/data`). No UI-facing fix shipped; a user who triggers this cache-miss path
  (e.g. via an ingest job that lands a new trading date) can still hit this backend crash today, exactly as
  before this iteration. This is a carried-forward, already-flagged critical issue awaiting an explicit
  owner decision (fix, scope, or formal defer) — not something this iteration changed for better or worse.
- **The `data_provider_runs` 120/121/122 finding** (that the observed 4-of-7 `aggregates_refreshed` outcome
  is design-consistent for two categories and a confirmed MemoryError for the third) is a documentation-only
  confirmation written into the dev handoff. It does not change what any `/data` job-history row displays to
  a user; the underlying persisted data and its rendering are unchanged.
- **The `demo.sh ops-hardening --session-live` walkthrough** for J-05/J-06 is still not produced — this
  iteration's own decomposer pass confirmed (by reading `scripts/automation/run-goal.sh`) that no autonomous
  mechanism in this framework produces it; it remains an open owner/framework decision, not something a user
  can access today or that this iteration attempted to build.
