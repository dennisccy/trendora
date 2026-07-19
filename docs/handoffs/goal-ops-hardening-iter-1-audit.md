# goal-ops-hardening-iter-1 Audit Report

**Date:** 2026-07-19
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01 (backfill honors the requested range; zero-work explained honestly) and J-03 (no per-run range
cap; date-window chunking) are genuinely implemented and end-to-end verified — the cadence bypass,
`dates_total` redefinition, breakdown arithmetic, `max_range_days` removal, and chunking all trace
correctly through the code, and the browser-qa-agent exercised every named journey against a live
backend with exact DOM assertions (17/17). The audit found **two real honesty defects in the new
exclusion-breakdown fields** — both tied to AG-3 ("displayed numbers must be the engine's real
computation") — and **fixed both surgically at their choke points with regression tests**: fabricated
`0`-value breakdowns on interrupted-backfill rows (observed and reproduced twice by browser-qa), and an
`error_other` undercount past 20 failures that would break the "invariants hold exactly" DoD criterion.
After the fixes, only GAP-level limitations remain (documented below), so the phase goal is achieved and
the system is materially more honest than it was pre-audit.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): interrupted-backfill rows displayed a fabricated `0 calendar days · 0 already snapshotted · 0 non-trading` breakdown for ranges that were really hundreds of days**

`_create_run_record` (`apps/backend/app/engine/data_manager.py:3044`) serializes `_run_detail(prog)` at
job **start**, when `prog` is a fresh `JobProgress` whose breakdown fields are still their dataclass
defaults (`calendar_days == 0`, etc. — they are only set later, inside `_do_backfill`). When a job's
process is killed mid-run, the boot sweep `sweep_orphaned_runs` (`:3119`) flips the row's status to
`interrupted` **without recomputing `message`**, so those job-start zeros persist forever. Because
`_run_detail` gated the four breakdown fields only on `_is_backfill_like` (`:3009-3012`, pre-fix), a
`backfill`/`both`/`rebuild` interrupted row served literal `0`s rather than `null`, and the frontend
`BackfillBreakdown` (which correctly suppresses only an **all-null** breakdown,
`apps/frontend/app/data/page.tsx:2519`) rendered "0 calendar days · 0 already snapshotted · 0
non-trading". This is exactly the "fabricated zero" pattern this iteration's own component docstring and
UT-10 explicitly guard against for other row kinds — a direct AG-3 violation. **The browser-qa-agent
independently discovered and reproduced this twice** (517-day interrupted jobs;
`reports/phase-goal-ops-hardening-iter-1-ui-test-results.md` UT-14 "Additional observation" + Additional
Observations #1) and recommended the backend fix; neither the reviewer nor QA acted on it.

*Fix applied:* `_run_detail` now serves the four breakdown fields only when `_breakdown_computed`
(`_is_backfill_like and prog.calendar_days > 0`) — since `calendar_days == (end - start).days + 1 >= 1`
for every real requested range, `calendar_days == 0` uniquely marks "breakdown not yet computed", so
job-start/interrupted rows serve `null` and the frontend suppresses them (matching the fetch/seed-load
convention). Verified by new test `test_run_detail_omits_breakdown_until_computed`
(`tests/test_data_manager.py:939`) — asserts a fresh 517-day backfill `prog` serves `None` for all four
fields while a computed one still serves the real 28/9/0/0. The interrupted/running-row path tests
(`test_running_row_visible_in_run_history_before_finish`,
`test_boot_sweep_marks_orphaned_running_as_interrupted`, +2 lifecycle) re-run green (4 passed).

**B2 — IMPORTANT (fixed): `error_other` silently undercounted past 20 failures, breaking the "invariants hold exactly" DoD criterion**

`_do_backfill` set `prog.error_other = len(prog.date_failures)` (`data_manager.py:2721`, pre-fix), but
`prog.date_failures` is a **bounded sample list** capped at `_MAX_ERROR_SAMPLES` (20) in
`_record_date_failure` (`:2396`). Once more than 20 in-range dates fail their compute/persist in one
backfill, `error_other` sticks at 20, so the DoD-item-4 invariant `snapshots_created +
already_snapshotted + error_other == dates_total` — which the spec requires to "hold exactly, never
approximated" (AG-3) — silently breaks, and the `/data` breakdown becomes self-contradictory. The same
file's `omitted` (bounded sample) / `omitted_total` (unconditional total) split is the correct
precedent, which was not followed. **The reviewer flagged this as MINOR** (out-of-scope, "no TC hits it
— all real paths hit 0 failures"). I took a stricter view for two reasons: (a) it defeats an explicit
DEFINITION OF DONE criterion tied to a *critical* anti-goal, and (b) this very iteration's J-03 removed
the range cap, so multi-hundred-day backfills are now reachable, making a >20-failure job materially
more likely than before. I was genuinely on the IMPORTANT/GAP boundary and, per the judgment rubric,
chose the higher level.

*Fix applied:* added an uncapped `date_failures_total: int` counter to `JobProgress` (`:1677`), bumped
unconditionally in `_record_date_failure` (`:2394`), and set `error_other` from it at both the
early-return (`:2571`) and the finalize (`:2723`) — mirroring the `omitted_total` precedent exactly.
Verified by new test `test_backfill_error_other_uncapped_past_sample_limit`
(`tests/test_data_manager.py:965`): forces 25 in-range dates to fail, asserts the sample list caps at 20
while `error_other == 25` and invariant 2 holds exactly. The five existing breakdown/invariant tests
(`test_backfill_breakdown_invariants_hold_on_fresh_and_rerun`, `test_backfill_create_once_immutable`,
`test_do_backfill_cadence_bypass_for_backfill_not_rebuild`, `weekend_span…`, `chunk_plan_derives…`)
re-run green — the fix is byte-identical for every ≤20-failure path (`date_failures_total ==
len(date_failures)` there).

**B3 — GAP (documented): the live `to_dict()` path still shows fabricated `0` breakdowns for a `both`-kind job during its fetch stage**

B1's fix corrects the **persisted** row (`_run_detail`), which is what browser-qa observed. The **live**
poll serialization `JobProgress.to_dict()` (`data_manager.py:1776-1781`) still emits the breakdown
fields unconditionally as ints, and the live `JobProgressPanel` renders `BackfillBreakdown` whenever
`showBackfill` is true — which for a `both` job is true during the **fetch** stage
(`apps/frontend/app/data/page.tsx:2612`), before `_do_backfill` sets `calendar_days`. So a live `both`
job transiently shows "0 calendar days · …" until its backfill stage starts. Left unfixed: **no
Must-have journey this iteration exercises `both`** (J-01/J-03 use `backfill`), it is transient (not a
persisted/durable wrong value), and the dev handoff already flagged `both`-kind display nuances. The
robust future fix is a one-line frontend guard — suppress `BackfillBreakdown` when `calendarDays` is
falsy (null **or** 0) rather than only when all four are null — which would cover the live path and be
defense-in-depth for the persisted path. Not fixed here to avoid frontend scope creep on an unobserved,
untestable (no frontend test harness) edge.

**B4 — GAP (documented, pre-disclosed): `rebuild`'s breakdown invariant does not hold exactly**

`_do_backfill` keeps `rebuild`'s cadence-filtered target selection (`data_manager.py:2545`,
`allowed = … if prog.kind in _REBUILD_KINDS`), so cadence-excluded in-range dates land in none of
`snapshots_created`/`already_snapshotted`/`error_other`, and invariant 2 does not hold exactly for
`rebuild`. This is transparently self-disclosed in the dev handoff Known Issues and the reviewer NOTE,
and is correctly out of scope (the spec pins `rebuild` behavior unchanged; TC-10 only checks its target
*set* stays cadence-filtered, which it does). No journey exercises `rebuild`'s breakdown numerically.
Acceptable; flag for whoever next owns `rebuild`'s contract.

### Frontend Findings

**F1 — GAP (documented): `LastRunSummary` shows "0 trading days in range" when the latest persisted run is an interrupted backfill**

With B1 fixed, an interrupted latest run's `BackfillBreakdown` is now correctly suppressed inside
`LastRunSummary`, but the line `{run.snapshots_created ?? "—"} snapshots · {run.dates_total ?? "—"}
trading days in range` (`apps/frontend/app/data/page.tsx:2560`) still renders "0 snapshots · 0 trading
days in range" for an interrupted run, because `dates_total` is served unconditionally by `_run_detail`
(a **pre-existing** field, not gated this iteration) and is 0 in the job-start state. This is milder
than B1 — it is paired with the neutral "interrupted" badge, which contextualizes the 0s as "did not
complete" rather than "0 work" — and `dates_total` gating is broader (used by the RunHistory "Dates"
column and existing tests), so it is out of surgical scope. Documented for a future iteration that
revisits interrupted-row rendering (deferred per the spec's "interrupted status semantics out of
scope").

### Test Findings

**T1 — OBSERVATION: the QA report understates the browser testing that actually happened**

`reports/qa/goal-ops-hardening-iter-1-qa.md` narrates browser tests TC-05/06/13/14 as SKIP/"deferred due
to page load complexity" and leans on API + code inspection. This materially **undersells** what was
done: the separate `browser-qa-agent` ran a full live walkthrough — 17/17 with exact `data-testid`/class
DOM reads and screenshots (`reports/phase-goal-ops-hardening-iter-1-ui-test-results.md`) — covering
reload preservation (UT-05, 36 rows stable), fresh-session fallback (UT-06, "from a previous session"),
interrupted badge (UT-14), and the readiness sequence (UT-15). The authoritative browser evidence is the
`ui-test-results.md`, not the QA report's summary. No product impact; a reporting-quality note so a
reader does not wrongly conclude the journeys went unverified in a browser.

**T2 — OBSERVATION: dev-added tests are high quality**

The 8 new/changed backend tests assert exact values and cover the right edges (mixed vs all-non-trading
range, chunk-plan arithmetic via a config override rather than a slow full run, cadence-bypass-vs-rebuild
with disjoint windows). The two coverage holes were exactly the two honesty edges this audit found
(>20 failures; interrupted-row breakdown) — now closed by B1/B2's regression tests.

---

## 3. Domain Assessment

The core domain logic is correct and the arithmetic is honest by construction:

- **Cadence bypass (J-01):** `allowed = _cadence_allowed_dates(…) if prog.kind in _REBUILD_KINDS else
  None` (`data_manager.py:2545`) is the right, minimal scoping — an explicit `backfill`/`both` range
  always wins, `rebuild` is untouched. Proven by `test_do_backfill_cadence_bypass_for_backfill_not_rebuild`
  (bypass snapshots all 3 cadence-excluded dates; a `rebuild` over a disjoint excluded window snapshots
  0) and browser UT-02/04 (May-2026 range that the cadence would previously have no-op'd now yields
  19/19).
- **`dates_total` redefinition + breakdown:** `dates_total = len(in_range)`;
  `non_trading_days = calendar_days - dates_total` (`:2537-2539`) — invariant 1 holds by construction.
  Every target lands in exactly one of {snapshot created, failure} (traced through `_persist_isolated`,
  `:2626-2647`), so invariant 2 holds exactly for `backfill`/`both` — now robustly, past the 20-failure
  cap, after B2.
- **Chunking + cap removal (J-03):** `_date_windows` (`:1932`) tiles `[start,end]` with no gaps/overlaps;
  the window loop advances `chunk_index` per window (`:2718`); `max_range_days` is gone from `config.py`,
  `config.yaml`, and `validate_job_request` (grep confirms 0 live references). Browser UT-12/13 showed a
  517-day range accepted, `chunk 0/6 → 1/6`, `dates_done 0 → 71 → 127`, no cap error; TC-7 (412-day) →
  `chunk_total=5`.
- **AG-8/AG-9:** the shared bar cache is loaded once per job (size bounded by universe breadth, not range
  length; `:2661` comment + verified in the loop), so large spans stay memory-bounded; no live network
  call is introduced (backfill remains seed-only). Both confirmed.

The honesty of the *breakdown feature* was the one soft spot — its happy path is immaculate, but its
unhappy paths (mass failure; interruption) fabricated or approximated numbers. That is precisely where an
audit should bite, and both are now fixed at their single choke points with tests.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py` | B1 — `_run_detail` serves the four breakdown fields as `null` unless `_breakdown_computed` (`calendar_days > 0`), so interrupted/running-row-at-start rows no longer emit fabricated `0`s (AG-3). |
| 2 | Important | `apps/backend/app/engine/data_manager.py` | B2 — added uncapped `date_failures_total` counter (bumped in `_record_date_failure`); `error_other` now derives from it, so invariant 2 holds exactly past `_MAX_ERROR_SAMPLES` (20) failures. |
| 3 | (test) | `apps/backend/tests/test_data_manager.py` | Added `test_run_detail_omits_breakdown_until_computed` (B1) and `test_backfill_error_other_uncapped_past_sample_limit` (B2). |

**Verification run (targeted, per this repo's no-full-suite rule):**
- `pytest -k test_run_detail_omits_breakdown_until_computed` → **1 passed** (0.23s).
- `pytest -k error_other_uncapped` → **1 passed** (70s).
- `pytest -k "breakdown_invariants or create_once_immutable or cadence_bypass or weekend_span or chunk_plan_derives"` → **5 passed** (no regression to dev's breakdown/invariant tests).
- `pytest tests/test_data_manager_jobs_pipeline.py -k "running_row_visible or boot_sweep or lifecycle_counts or run_record"` → **4 passed** (B1 touches this `_run_detail`/`_create_run_record`/sweep path).

All changes are backend-only, confined to `_run_detail`, `_record_date_failure`, `_do_backfill`, and the
`JobProgress` dataclass; the `git diff` contains no stray edits. No dev/frontend handoff claim was
invalidated — the fixes make the implementation actually honor the `BackfillBreakdown` "never a
fabricated 0" contract the handoffs already asserted.

---

## 5. Recommended Next Step

**Proceed.** The iteration achieves both target journeys and does not regress J-04, and the two
IMPORTANT honesty defects are fixed and tested. Carry these documented GAPs into the session's
lessons/backlog rather than blocking:

1. **B3 (recommended small fix, next iteration):** change `BackfillBreakdown`'s suppression guard from
   "all four null" to "`calendarDays` falsy" — one line that closes the live `both`-during-fetch
   fabricated-zero and is defense-in-depth for the persisted path.
2. **F1 / B4:** when a future iteration revisits interrupted-row rendering or `rebuild`'s own contract
   (both explicitly deferred here), null-out `dates_total` for uncomputed rows and decide `rebuild`'s
   fifth cadence-excluded bucket.
3. **T1:** the pipeline should prefer the `browser-qa-agent`'s `ui-test-results.md` as the authoritative
   browser evidence; the QA report's "deferred" wording is misleading for a run that was, in fact,
   fully browser-exercised.
