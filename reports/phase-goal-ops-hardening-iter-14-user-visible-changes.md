# Phase goal-ops-hardening-iter-14 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status`/`git
diff --stat`: only `apps/backend/app/engine/forward_testing.py` [modified], two new backend test
files, and `reports/perf-budgets.md` [modified — a non-UI reporting artifact] changed). The plan's
`Frontend Present: no` is literally accurate. However, per this dispatch's PUMP NOTE, that flag is not
read as "nothing to report" here: the rewritten function (`compute_forward_aggregates`) is the sole
compute path behind an EXISTING, already-consumed endpoint (`GET /api/backtest`) and an EXISTING
ingest finalize step, and this iteration's entire purpose is an availability/resilience fix — closing
a failure mode (iter-7, iter-13) that was directly visible to a user as a frozen readiness badge or an
unresponsive app. That is real, testable, user-facing behavior even though no frontend file changed a
single line. This report documents it as a **behavior change**, not a new feature — matching the phase
spec's own framing ("no visible surface changes when the fix holds; the delta is the ABSENCE of the
frozen/blank-frame failure mode").

---

## What Users Can Now Do

None. This iteration adds no new user action or capability — confirmed by the phase spec itself ("New
user-facing capability: None new", "New user actions: None") and by the diff (zero frontend files
touched, and the rewritten function's output is proven byte-identical to before, across all 5
configured horizons with and without `as_of` — TC-1/TC-2). The nearest thing to a new capability is a
reliability guarantee for existing surfaces, described under "What Old Behavior Changed" below.

---

## What Changed in the Visible UI

None directly. No page, component, label, or layout was edited — everything a user sees today looks
and reads exactly as it did before this iteration. The change is entirely underneath three EXISTING
surfaces' runtime behavior under one specific condition (heavy forward-aggregate computation); see
"What Old Behavior Changed" below.

---

## What Old Behavior Changed

- **Global readiness badge (top bar, every page — `HealthBadge`, `data-testid="readiness-badge"`):**
  on this session's grown data basis (`scanner_results`/`forward_returns` both ~9x their last-measured
  size), the computation behind this badge's data twice caused an availability failure under load —
  iter-7's original defect, and iter-13's escalation to a ~12-minute full-backend wedge under 4
  concurrent backfills + a diagnostic read, needing an operator hard-restart. During that kind of event
  a user would see the badge stuck on its "Checking backend…" loading state (or, if the backend became
  fully unreachable, "Backend unavailable") for the duration of the wedge, unable to do anything else
  in the app. This iteration's rewrite removes the unbounded, whole-table read that caused it. Evidence
  so far is non-browser: a real tightened-`ulimit -v` subprocess test proves the new code succeeds
  where the old code needed roughly 2.3x the memory (TC-3); a 4-thread concurrent-caller test against a
  shared DB shows no hang (TC-4); and one live, full-deep-basis warm recorded 250/250 `GET /api/health`
  polls returning HTTP 200 with no frozen window across a 278-second warm (TC-5) — the first time this
  basis size has completed this warm at all (iters 11-13 each hit `MemoryError` at this exact step).
  The in-browser confirmation that the badge itself never freezes during a real, live backfill (TC-9)
  has not been captured yet — see "Not Visible Yet."
- **`/backtest` page's per-horizon evidence panel:** previously could hang on its loading skeleton or
  fall back to the "Backend unavailable" error card if a `GET /api/backtest` cache-miss triggered the
  same unbounded computation under memory pressure. Same fix, same evidence status as above — proven
  at the API/process level, not yet browser-confirmed.
- **`/data` page's post-job "Refreshed: ..." summary line (`data-testid="aggregates-refreshed"`):**
  "forward aggregates" was already one of the possible comma-separated entries in this line before this
  iteration (the ingest finalize hook that produces it, `_refresh_ingest_aggregates`, is byte-unchanged
  this iteration). But it could be silently absent if the per-horizon warm loop hit a memory error on
  its very first horizon (before any horizon succeeded). That specific drop condition is closed for
  ordinary load now that the underlying read no longer exhausts memory at this table size — the entry
  should appear more consistently after a backfill that changes the latest run's forward-return
  aggregate. Not yet browser-confirmed either.

---

## Not Visible Yet

- **Live, in-browser proof that the readiness badge and `/backtest` never freeze under a real backfill
  (TC-9)** has not been captured. It is the browser-qa-agent's pass this iteration (regression replay
  of J-01/J-03/J-05 plus one `/backtest` load, per TESTING REQUIREMENTS) — the next pipeline stage
  after this report, not something the developer stage or this analysis produces evidence for.
- **A live memory-pressure induction on the actual measured full-deep-basis process (TC-6)** was not
  performed — the operator judged inducing artificial pressure on that live process unjustified given
  this host's crash history (two hardware resets under ingest bursts, 2026-07-20/21). The evidence for
  TC-6 is indirect: a synthetic-fixture induction (TC-3, a different, throwaway process) plus the
  absence of any organic memory error during one clean 278-second full-basis warm (TC-5). The evaluator
  decides whether that is sufficient; this report does not assume it is.
