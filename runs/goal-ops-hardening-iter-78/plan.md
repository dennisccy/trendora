# goal-ops-hardening-iter-78 Execution Plan

## Context check

Prior verdict was ESCALATE (mandatory full-depth + full regression widen, per goal.md's loop
mechanics and the phase spec's own "Full trigger: 3"). All 8 Must-have journeys currently pass;
this iteration is a consolidation pass closing three agent-owned items iter-77's own evaluator
flagged as blocking clean closure — no new Must-have journey, no new Data Contract value. It
advances goal.md's Key Capability 4/5 ("the UI tells the truth about the backend's own state") and
the Vision's "operationally solid ... honest about its own state" without touching any frozen
surface (`app.engine.readiness` server logic, `compute_forward_aggregates`, the J-05..J-09
goldens). No contradiction with goal.md found; no scope creep — every OUT OF SCOPE item in the
phase spec is correctly an owner-gated carry, not silently dropped.

Canonical-artifact naming note (assumption, not a phase-spec typo): the spec's
`goal-ops-hardening-iter-78-ui-test-results.md` maps to this project's actual established path
`reports/phase-goal-ops-hardening-iter-78-ui-test-results.md` (iter-77's equivalent is
`reports/phase-goal-ops-hardening-iter-77-ui-test-results.md`). All lanes must write/merge there —
this is the exact "unmerged side-file" mistake (iter-77's `devfix-replay/`) the spec calls out to
avoid repeating.

## What to Build

- **Launcher residue purge** (`scripts/start-frontend.sh`, tracked source is
  `incredible_auto_dev/scripts/start-frontend.sh`): before the existing staleness-check /
  build-if-stale decision, actively delete `apps/frontend/__tc3_intentionally_broken.ts` and any
  `apps/frontend/.next-test-*` scratch dir if present, logging what was purged. This is the exact
  filename/glob `test_start_frontend_script.py`'s own `_purge_test_residue()` /
  `_pristine_frontend_tree` autouse fixture already reserves and cleans on ITS OWN setup/teardown —
  reuse those same two literals in the shell script rather than inventing new ones, so the two stay
  in lockstep. If the purge step itself fails (e.g. permission error), the launcher must fail LOUD
  with a clear log line and non-zero exit — never silently serve a stale/broken build. The
  HOST-GUARD block (lines ~28-58) and the iter-77 `flock` build-lock stay byte-unchanged (AG-10,
  binding — reviewer/auditor should diff-check this specifically).
- **New regression test** in `apps/backend/tests/test_start_frontend_script.py` (or a sibling
  file) that writes the residue file directly INSIDE the test body — i.e. after the module's own
  autouse `_pristine_frontend_tree` setup-purge has already run, simulating "a different process
  wrote it and this module is not the next thing invoked" — then runs the REAL
  `scripts/start-frontend.sh` end-to-end and asserts rc 0 + a live-serving `next start`. This
  proves the LAUNCHER's own defense, not the test module's pre-existing self-heal. Reuse the
  module's existing helpers (`_Launcher`, `_owning_pid`, `_scratch_dist_name`,
  `_assert_page_fully_styled`-style checks) rather than duplicating them — the module already has
  this exact shape of test (`test_broken_source_fails_build_and_leaves_no_stray_process`, TC-3) to
  pattern-match against, just asserting the opposite outcome (success, not failure).
- **J-09 walkthrough-capture fix**: the "background compute in flight" gallery frame currently
  captures an idle Ready-only state (iter-77/e). Two components are likely both needed: (1) a
  reliable trigger — target/force an as-of date whose evidence genuinely still needs on-demand
  dispatch for the CURRENT dataset version, not just "one day back" (which is idle whenever nothing
  changed the dataset version since the last full warm for that date — see
  `runs/goal-session-ops-hardening/journey-scripts/J-09.json`'s own step notes for how the browser-qa
  golden reliably gets a real window via "Previous available date", and
  `reports/goal-session-ops-hardening-demo.json` steps 14-15 for the proven direct
  `/backtest?asof=<date>` pattern that "already captures this scene correctly per iter-25"); (2) an
  explicit wait for the compute-chip to actually render (`background-compute-indicator` on the
  badge / `background-compute-active-row` testid on `/data`, both already shipped in
  `apps/frontend/app/data/page.tsx`) before the screenshot fires — not merely the generic
  network-idle/text-appeared heuristic in `scripts/automation/lib/demo_runner.py`'s
  `_settle_for_capture`/`_check_expect`, which is what let iter-77's step capture too early. Fix
  whichever layer is the actual root cause first (investigate before coding, per TDD) — the shared
  capture engine (`demo_runner.py`) if the wait primitive itself is generic/reusable, and/or this
  iteration's own per-iteration demo step JSON (iter-77 precedent: the developer directly edited
  `reports/phase-goal-ops-hardening-iter-77-demo.json` step 7's target key as part of "Backend"
  in-scope work). Timing/trigger fix only — `get_background_compute_status()` and every Data
  Contract value stay untouched.
- **Client-side staleness tick** (`apps/frontend/components/readiness-provider.tsx`): on each
  successful `GET /api/health` poll, record `stale_for_s` alongside the client wall-clock time it
  was received at. Add a local 1-second interval that re-derives a LIVE staleness value (base +
  elapsed client seconds since receipt) so the value the provider exposes increases smoothly
  between polls instead of freezing. `health-badge.tsx` and `preflight-banner.tsx` already consume
  `staleForS` from `useReadiness()` via the single shared `formatStaleAnnotation()` call each — they
  should need NO changes if the provider itself re-renders every tick with the updated value; do
  not add a second formatter or a second poll.
- **Pure tick-derivation helper**: extract the math into a new export alongside
  `apps/frontend/lib/staleness-annotation.ts` (e.g. a sibling function/file), unit-tested with a new
  plain-`node` test file mirroring `lib/staleness-annotation.test.ts`'s existing convention
  (`node lib/<new-file>.test.ts`). The derived live value must still be fed through
  `formatStaleAnnotation` as the single formatting authority — never a second formatter, and the
  existing null/0/negative/non-finite guards must keep applying to the DERIVED value (e.g. a
  `null` base from a failed poll must never start ticking upward into a fabricated number).
- **Re-verification**: J-04, J-07, J-09 via browser-qa-agent, results merged into THIS iteration's
  canonical `reports/phase-goal-ops-hardening-iter-78-ui-test-results.md` (never a side file — the
  iter-77 mistake this spec explicitly calls out). Post-ESCALATE full regression widen: J-01, J-03,
  J-05, J-06, J-08 must also replay green (deterministic replay or LLM fallback, no
  `pending_infra`). Any mid-round fix-mode QA retry must write back into this SAME canonical file.

## Agents Required

- developer: yes -- implements all four in-scope code items (launcher purge + its regression test,
  the walkthrough-capture trigger/wait fix, the readiness-provider tick + pure helper + its unit
  test)
- backend-data: yes -- the launcher purge and its regression test
  (`apps/backend/tests/test_start_frontend_script.py`) and the walkthrough-capture script fix are
  backend/tooling-scoped, real-process/real-build tests
- frontend-ux: yes -- the readiness-provider tick + pure helper touch the global readiness
  badge/preflight banner surface present on every page

## Frontend Present
yes

## Files to Create/Modify

- `incredible_auto_dev/scripts/start-frontend.sh` (= `scripts/start-frontend.sh`) -- add the
  residue-purge step before the staleness check; loud purge-failure handling; HOST-GUARD block and
  `flock` build-lock byte-unchanged.
- `apps/backend/tests/test_start_frontend_script.py` -- new regression test for the launcher's own
  residue defense (writes residue after module setup, runs the real script, asserts clean serve).
- `scripts/automation/lib/demo_runner.py` and/or `reports/phase-goal-ops-hardening-iter-78-demo.json`
  -- fix the J-09 background-compute walkthrough trigger/wait so the captured frame shows compute
  in flight.
- `apps/frontend/components/readiness-provider.tsx` -- receipt-time tracking + 1s tick producing a
  live `staleForS`.
- `apps/frontend/lib/staleness-annotation.ts` or a new sibling `lib/*.ts` file -- pure tick-derivation
  export.
- New `lib/*.test.ts` file for the tick helper (plain-`node` convention).
- `docs/handoffs/goal-ops-hardening-iter-78-dev.md` -- dev handoff (DoD requirement).

## UI Evolution

- New user-facing capability: none new -- refines the existing "as of Ns ago" annotation (iter-77)
  to update continuously instead of freezing between polls, and removes a known way the whole
  frontend could fail to start.
- New information displayed: none -- no new field, no new payload key; purely a client-side
  re-derivation of the already-served `stale_for_s`.
- New user actions: none.
- UI surface changes: the global readiness badge and preflight banner (present on every page) now
  tick their staleness text every second instead of only refreshing on poll landing. No new page,
  panel, or card.
- Navigation changes: none.

## Visual Requirements

- Component patterns: no new components -- reuse the existing badge pill / banner strip; the
  staleness annotation stays plain inline text (`data-testid="readiness-staleness"` /
  `"preflight-staleness"`), styling unchanged.
- Layout: unchanged -- the header's existing `flex-wrap` (iter-77 fix) already accommodates the
  annotation alongside the pill and the background-compute chip; no new layout work expected.
- Key visual effects: none new -- calm, factual, unmissable text per the project's existing "quiet
  proven/not-proven chip" mood; no animation beyond the displayed number changing every second.
- States to handle: `stale_for_s === null` (failed poll) must render nothing even while the tick
  timer is running (TC-4); `stale_for_s === 0` (fresh compute) renders nothing; ticking must never
  bypass `formatStaleAnnotation`'s existing guards or introduce a second formatter.

## Key Test Scenarios

- TC-1: `apps/frontend/__tc3_intentionally_broken.ts` present in the live tree -> launcher purges
  it, `next build` exits 0, `next start` binds the port and serves HTTP 200 on `/`.
- TC-2: normal tree, no residue -> the purge step deletes nothing and the build/skip-rebuild
  decision is byte-identical to pre-iteration behavior.
- Purge-failure case: purge itself errors (e.g. permission denied) -> launcher fails loud with a
  clear log line, never silently serves a stale/broken build.
- TC-3: badge shows "as of 5s ago" from a landed poll; 10 more seconds elapse with no new poll ->
  annotation reads ~"as of 15s ago" (ticking every 1s), not frozen.
- TC-4: `stale_for_s` is `0` or the last poll failed (`staleForS === null`) -> no annotation renders
  even as the 1s tick timer fires.
- TC-5: a `/backtest` request targets a historical as-of date whose evidence needs on-demand
  dispatch -> the J-09 walkthrough capture's "background compute in flight" frame shows
  "background compute running (N)" alongside "Ready" -- not an idle Ready-only frame.
- TC-6: this iteration's fresh full regression pass -> J-04/J-07/J-09 land in
  `reports/phase-goal-ops-hardening-iter-78-ui-test-results.md` with PASS rows -- not a side/devfix
  file.
- TC-7: J-01, J-03, J-05, J-06, J-08 all remain PASS on this iteration's post-ESCALATE full
  regression (deterministic replay or LLM fallback, no `pending_infra`).
- TC-8: `scripts/start-frontend.sh`'s HOST-GUARD block and `flock` build-lock are byte-identical to
  their pre-iteration form when this iteration's diff is reviewed (AG-10 regression check).

## Out of scope (carried, per phase spec — do not implement)

- `closure_gate.py:72`'s backend-only regex false positive, `browser-qa-phase.sh`'s ordering bug,
  B-1107, the 2s health-ceiling scope question, and the finish-now-vs-clear-notes question — all
  owner-permission-pending, restated in the phase spec's NOTES, not decided here.
- Any change to `app.engine.readiness` cache/staleness/tick SERVER logic or
  `compute_forward_aggregates` (binding "Do not redo" -- this iteration's fix is client-side only).
- Any change to `journey-scripts/J-*.json` goldens (binding "Never regenerate the J-05..J-09
  goldens").
- J-05/J-07's own `[NEW]` walkthrough captures, J-06's perf-budgets entry, J-01's zero-work-panel
  photograph, and the Regime Lab backlog item -- stay carried, excluded to keep this iteration's
  diff small per the phase spec's own rule 4.
