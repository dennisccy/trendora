# Phase goal-ops-hardening-iter-53 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Written by:** ui-impact-analyst

---

## Scope note (read before the sections below)

`runs/goal-ops-hardening-iter-53/plan.md` and the phase spec both mark **Frontend Present: no**, and that
is correct at the file level: `git diff --stat` and `git status --porcelain` for `apps/frontend/` are both
**empty** (independently re-verified this session, not assumed). Every changed file is backend:
`apps/backend/app/engine/{universe_resolver,market_phase,data_manager}.py`, five backend test files, and
`reports/perf-budgets.md`.

However — exactly as this iteration's own `plan.md` warns pipeline automation not to misread "Frontend
Present: no" as "skip browser QA" — the phase spec's **"Product surface delta"** section names a real,
user-observable target: while a heavy fetch/backfill/rebuild job's `coverage_membership_timeline_refresh`
and `market_phase_warm` finalize-tail steps run, `GET /api/health` should stop going completely unanswered
*because of those two steps specifically*. This analyst independently re-read the actual (unmodified)
frontend source — `components/health-badge.tsx`, `components/readiness-provider.tsx`,
`components/preflight-banner.tsx`, `app/data/page.tsx`, `app/page.tsx` — to confirm exactly how the failure
state renders and which on-screen elements consume the two treated functions' stored output, then
cross-checked both against the developer's own live concurrent drill (`reports/perf-budgets.md` Item X /
Addendum 15, re-run with the same methodology as the prior iteration's Addendum 14).

**The honest result: the target was achieved for the two phases this iteration aimed at — narrowing, not
closing, the surrounding picture.**

- Both treated phases now measure **zero** connection-level `/api/health` non-answers in the live
  concurrent drill, down from 2 (both of which landed in exactly these two phases in the prior drill).
- The drill still recorded **one** non-answer overall (down from two, not down to zero) — it relocated to
  a third, adjacent finalize-tail step (`per_date_coverage_warm`) this iteration did not profile or treat.
- Both treated phases got faster in isolation under the same concurrent load
  (`market_phase_warm`: 26.26s → 0.73s, ~36x faster; `coverage_membership_timeline_refresh`: 46.05s →
  40.54s) — but the job's total finalize-tail time is measured **worse** this run (1,559.30s vs
  1,261.42s — 29.9% over the ~1,200s/20-minute target, vs 5.1% over previously). The developer's own
  analysis attributes essentially the entire increase to two OTHER, unmodified steps subject to
  run-to-run scheduling variance, not to anything this iteration changed.

This report documents that mixed-but-real, partially-positive finding instead of a flat "nothing changed"
stub, so the browser-qa lane (J-04's first-ever evidence capture, plus J-05/J-07's health-responsiveness
replay) has the concrete detail it needs.

---

## What Users Can Now Do

**Nothing new as a feature, page, field, or button.** The one thing that changed is how reliably two
already-running background steps behave while a data job is in flight:

- While a backfill/rebuild job's `coverage_membership_timeline_refresh` step runs, the top-bar readiness
  badge and the full-width preflight banner (present on every page, both unchanged in code) are no longer
  measured to flip to their red "Backend unavailable" / "NO-GO — do not rely on today's board." state
  *because of that specific step* — the developer's live drill measured zero such occurrences from this
  step, down from 1 in the prior drill.
- The same is true for the `market_phase_warm` step — zero occurrences now, down from 1 in the prior
  drill, and the step itself finished vastly faster (26.26s → 0.73s of concurrent-load elapsed time).
- **This is not the same as "the badge never flips red during a job."** The live drill still recorded one
  connection-level non-answer overall, now traced to a third, neighboring step
  (`per_date_coverage_warm`) this iteration did not touch. A user watching the badge during a long job may
  still occasionally see a red flip — just not one caused by the two steps this iteration fixed.
- The two new automated fault-injection tests (deliberately breaking one of the two newly-treated steps to
  prove the app survives it without crashing) are developer/QA verification tools, opt-in and code-only —
  not something a user or operator triggers through the running UI. See "Not Visible Yet" below.

## What Changed in the Visible UI

**Nothing in code.** Zero UI elements were added, removed, relabeled, or restyled — `apps/frontend/` has a
completely empty `git diff --stat` / `git status --porcelain` for this iteration (independently verified).

The elements most relevant to this iteration's target are present and **unchanged in code**:

- The readiness pill in the top-right of every page's header (`HealthBadge`,
  `data-testid="readiness-badge"`) — the same five states as before (`Checking backend…`, `Ready`,
  `Initializing… history n/m`, `Snapshot pending — …`, `Backend unavailable`). Only the backend's
  *frequency* of reaching the last state because of the two treated steps was targeted.
- The full-width banner directly below the header (`PreflightBanner`, `data-testid="preflight-banner"`) —
  the same GO / DEGRADED / NO-GO states, same exact wording ("NO-GO — do not rely on today's board.",
  "Backend is unavailable — the preflight check could not run."). Unchanged in code.
- The Dashboard's "Market Phase & Severity" card (`app/page.tsx`, `PhaseGlanceCard`) — the on-screen
  consumer of `market_phase.compute_market_phase`'s stored output, the exact function this iteration
  bounded. Unchanged in code; its displayed phase label, 0–100 severity score, and component breakdown
  must read identically to before this iteration (proven by three new byte-identity unit tests in
  `test_market_phase.py`, not by a UI change).
- The `/data` page's "Dataset coverage," "Universe resolution as of …," and membership-timeline panels —
  the on-screen consumers of `coverage_membership_timeline_refresh`'s stored output. Unchanged in code;
  values must read identically to before (proven by a new byte-identity integration test in
  `test_data_manager_membership_cache.py` plus four new tests in `test_universe_resolver.py`).

## What Old Behavior Changed

- **The specific "Backend unavailable" trigger this iteration targeted is gone, measured rather than
  assumed.** Neither treated phase produced a connection-level non-answer in the re-run drill, versus 2
  (both attributed to these exact two phases) in the prior drill.
- **The overall picture improved but did not close — stated honestly, not rounded up.** The drill still
  recorded 1 non-answer overall (down from 2), now inside a different, untreated step
  (`per_date_coverage_warm`, the per-date coverage-snapshot persist loop). Reaching zero system-wide would
  need that step profiled and treated the same way, in a future pass.
- **A heavy backfill/rebuild job's total time under concurrent traffic is measured worse this run, for
  reasons unrelated to what this iteration changed.** The "Job progress" status badge on `/data` staying in
  a running state is now measured at 1,559.30s (29.9% over the ~1,200s/20-minute target) versus 1,261.42s
  (5.1% over) previously. The developer's own analysis: essentially the entire increase traces to one
  untouched step whose finalize-tail cost depends on scheduling luck against a concurrent research-request
  stream (`factor_lab_all_warm`, 0.05s → 496.28s) plus an unexplained spike in another untouched step
  (`forward_aggregates_warm`, one horizon: 88.35s → 368.50s). Both steps this iteration actually modified
  got faster, not slower. An operator watching a job on a date resembling this run could see a longer
  overall wait than before this iteration, even though the specific reliability problem targeted this
  iteration improved.
- **A previously-missing memory-recovery path was added for `coverage_membership_timeline_refresh`.**
  Before this iteration, if that specific step ran out of memory it fell through to a generic error handler
  with no dedicated `_release_process_memory()` call — unlike three sibling finalize-tail steps, which
  already had one. It now matches them. The user-visible outcome is unchanged (that step's category was
  already honestly left out of the `/data` "Refreshed:" list on a memory error, both before and after this
  iteration); what changed is how cleanly the backend recovers memory afterward — not something a user
  directly observes, but it reduces the chance of a subsequent stall.

## Not Visible Yet

- **The relocated non-answer** (`per_date_coverage_warm`) is a newly-identified, unfixed finding from this
  iteration's own drill — not something a future browser session will see resolved yet.
- **The finalize-tail budget overage remains open.** The two largest untouched contributors
  (`forward_aggregates_warm`, `drawdown_expectations_warm`) are unchanged; closing the ~1,200s budget line
  is explicitly deferred to a future iteration.
- **J-04's badge/banner/logfile evidence (steps 3–5)** — already-shipped, unchanged code — is expected to
  get its FIRST screenshot/DOM/logfile evidence capture from this iteration's browser-qa lane. Until that
  lane runs, this remains proven only by code reading and by earlier journeys' step 1–2 assertions, not by
  captured visual/log evidence.
- **The Regime Lab `/research/regime-lab` MemoryError** (a separate, undiagnosed defect tracked as `J-06`)
  — explicitly out of scope this iteration; still unresolved.
- **The new fault-injection sites** (`coverage_membership_timeline`, `market_phase`) are reachable only via
  a `TRENDORA_FAULT_INJECT_MEMORY_ERROR` environment variable before `scripts/start-backend.sh` starts — a
  developer/QA verification hook, not something exposed anywhere in the running product's UI.
