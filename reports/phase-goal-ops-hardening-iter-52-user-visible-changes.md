# Phase goal-ops-hardening-iter-52 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-52
**Date:** 2026-08-07
**Written by:** ui-impact-analyst

---

## Scope note (read before the sections below)

`runs/goal-ops-hardening-iter-52/plan.md` and the phase spec both mark **Frontend Present: no**, and that
is correct at the file level: `git diff --stat` for this iteration touches only
`apps/backend/app/engine/{data_manager,research,forward_testing}.py`, their tests, and
`reports/perf-budgets.md` — confirmed empty for `apps/frontend/` (verified directly, not assumed). However,
exactly like iter-51 before it, the phase spec's own **"New user-facing capability"** and **"Product surface
delta"** sections name a real, deliberate, user-observable *target*: stopping the global readiness badge and
preflight banner (both already existing, unchanged this iteration) from flashing to their "backend
unavailable" failure state during a heavy data-loading job. This analyst independently read the actual
(unmodified) frontend source — `components/health-badge.tsx`, `components/readiness-provider.tsx`,
`components/preflight-banner.tsx`, all mounted globally in `app/layout.tsx` — to confirm exactly how that
failure state renders, then cross-checked it against the developer's own live measurement
(`reports/perf-budgets.md` Item U / Addendum 12).

**The honest result: the target was not met.** A flat "no user-visible changes" stub would therefore be
factually incomplete — it would hide the fact that this iteration's live measurement shows the specific
condition it targeted did not improve, and by the one measurement taken, got worse. This report documents
that narrow, real, and negative finding instead of stubbing it out, so the next lane (browser-qa-agent's
J-05/J-07 concurrent checks) has the concrete detail it needs.

---

## What Users Can Now Do

**Nothing new.** This is the central finding, stated plainly rather than buried:

- The one behavior this iteration targeted — the top-bar readiness badge and the full-width preflight
  banner (present on every page) no longer flashing to their red "unavailable" state while a heavy
  fetch/backfill/rebuild job's longest step runs — was **not achieved**. The developer's own real, solo,
  in-app measurement (`reports/perf-budgets.md` Item U / Addendum 12) found the backend's `/api/health`
  endpoint went completely unanswered (a connection-level non-answer — no response at all, not merely a
  slow one) **22 times** during one full timed job, versus **9 times** in the equivalent pre-fix measurement
  from iter-51 (Addendum 11). The count moved in the wrong direction.
- The new automated test that intentionally breaks one background calculation during a real data job (to
  prove the app survives it without a restart) is a developer/QA verification tool — opt-in, not part of
  the normal test run, and not something a user or operator interacts with. See "Not Visible Yet" below.

## What Changed in the Visible UI

**Nothing.** Zero UI elements were added, removed, relabeled, or restyled — `apps/frontend/` has a
completely empty `git diff --stat` for this iteration (independently verified).

The two elements most relevant to this iteration's goal are both present and both **unchanged in code**:

- The readiness pill in the top-right of every page's header (`HealthBadge`, `data-testid="readiness-badge"`)
  — already flips to a red "Backend unavailable" state whenever a periodic health check gets no response at
  all. That rendering logic is exactly as it was before this iteration.
- The full-width banner directly below the header on every page (`PreflightBanner`,
  `data-testid="preflight-banner"`) — already flips to a loud red "NO-GO — do not rely on today's board /
  Backend is unavailable — the preflight check could not run." banner under the identical condition. Also
  unchanged in code.

Neither element's appearance, wording, or trigger condition changed this iteration — only the backend's
*frequency* of triggering that pre-existing failure condition was targeted, and (per the finding above) not
successfully reduced.

## What Old Behavior Changed

- **The connection-level "backend unavailable" failure condition got measurably more frequent, not less, in
  the one drill performed.** 22 non-answers this iteration's live drill vs. 9 in iter-51's equivalent
  pre-fix drill. 19 of the 22 cluster inside the same single longest phase (`factor_lab_all_warm`, the
  Factor Lab page's background pre-compute) this iteration specifically targeted with scheduling fixes —
  the fix's yield points are confirmed (by unit test) to fire exactly as designed, but a code-grounded
  hypothesis in the addendum suggests one internal sort operation inside that phase cannot be interrupted by
  a yield point placed before it starts.
- **A newly-identified failure window, not previously known.** 3 of the 22 non-answers happened very early
  in the job (job-start +24s/+29s/+40s) — during the initial snapshot-write stage, *before* the finalize-tail
  warm phases (this iteration's actual target) even begin. This is a new, disclosed-but-unfixed finding, not
  something this iteration introduced in the sense of new code — it is a pre-existing gap this iteration's
  more thorough measurement happened to surface for the first time.
- **A heavy backfill/rebuild job can take noticeably longer to finish than the product's existing ~20-minute
  (1,200s) commitment.** An operator watching the "Job progress" card's status badge (`data-testid=
  "job-status"`) on `/data` would, on a date resembling this iteration's own measured run, see it stay in
  "running" well past 20 minutes — the developer's own drill reached 1,670.95s (~27.8 minutes) of measured
  finalize-tail time with one background step still incomplete when the drill's own 30-minute measurement
  window closed. The developer's analysis attributes most of this specific overage to the chosen date's own
  data volume rather than to this iteration's scheduling change itself (whose own isolated overhead was a
  smaller +20.4% on one phase) — but the overage is real and disclosed, not silently absorbed.
- **Of the health checks that did get an answer, more arrived slowly.** 94 of 1,471 successful polls (6.4%)
  took longer than the product's own 2-second responsiveness ceiling this run, versus 0 of 644 in iter-51's
  equivalent solo baseline.

## Not Visible Yet

- **The new fault-injection test** (`test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_
  stays_live`) is an opt-in, heavy (~14 minutes), developer/QA-only automated test gated behind
  `TRENDORA_RUN_HEAVY_INGEST_TEST=1`. It proves (via a real ingest job against a throwaway spawned backend,
  not a live request) that a deliberately-broken background calculation is honestly left out of the job's
  "refreshed" list while everything else still completes and the health check keeps answering — but this is
  not something reachable through the running product's UI.
- **The concurrent scenario** — a user actively viewing the Factor Lab or Factor Combination page while a
  heavy job runs in the background — was not measured this iteration (the developer's own drill was solo,
  no competing request). Given the solo result is already decisively negative, the concurrent case is
  expected to be at least as bad, not better, but this is not yet confirmed by any measurement. It is
  deferred to the browser-qa-agent lane (TC-2).
- **The Factor Lab page's real-browser load-time measurement** (time-to-interactive plus on-load API
  latency) was planned for this iteration's addendum but not yet captured — also deferred to the
  browser-qa-agent lane (TC-7).
