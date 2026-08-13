# goal-ops-hardening-iter-78 Dev Handoff

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Agent:** developer
**Status:** complete

## What Was Built

- **Frontend launcher residue purge** (`scripts/start-frontend.sh`, tracked source
  `incredible_auto_dev/scripts/start-frontend.sh`): before the existing staleness-check /
  build-if-stale decision, the launcher now unconditionally purges the two known
  test-residue artifacts a hard-killed `test_start_frontend_script.py` run can leave in the
  live `apps/frontend` tree — the exact filename `__tc3_intentionally_broken.ts` and any
  `.next-test-*` scratch dist dir — logging what was purged. A purge failure (e.g.
  permission error) makes the launcher fail loud with a clear log line and non-zero exit,
  never a silent fallback to a stale/broken build. The purge deliberately EXCLUDES this
  invocation's own `$NEXT_DIST_DIR` target from the `.next-test-*` glob (see "Bug found and
  fixed" below) so a test that legitimately reuses the same scratch dist dir across several
  sequential launcher invocations is never treated as if it were someone else's leftover.
  The HOST-GUARD block and the `flock` build-lock are byte-unchanged (confirmed via `git
  diff`; see Files Changed).
- **New regression test** `test_launcher_purges_leftover_test_residue_from_a_different_process`
  in `apps/backend/tests/test_start_frontend_script.py`: writes the residue file directly in
  the test body (i.e. after the module's own autouse setup-purge already ran, simulating "a
  different process wrote it"), then runs the REAL `scripts/start-frontend.sh` end-to-end and
  asserts a clean build, a fully-styled served page, the launcher's own purge log line, and
  that both the residue file and an orphan scratch dir are gone. This proves the LAUNCHER's own
  defense, not the test module's pre-existing self-heal.
- **J-09 walkthrough-capture timing fix** (`scripts/automation/lib/demo_runner.py`): raised the
  per-step wait ceiling so a step can opt into waiting up to 45s (via its own `timeout_ms`)
  instead of being hard-capped at 20s regardless of what it asked for. Root cause (confirmed by
  direct code reading, not assumed): the frontend's readiness badge backs off to a 30-second
  poll cadence once steady-state `Ready` (`health_poll_idle_interval_seconds: 30.0`,
  `config.yaml`), so a walkthrough step waiting for the background-compute chip to appear can
  never observe it within a 20s ceiling — a structural bug in the shared capture engine,
  independent of which JSON content a given demo step uses. Two new self-tests added; the
  existing `default_timeout_ms` fallback (used by steps that do NOT set their own
  `timeout_ms`) is unchanged, so this is additive, not a blanket slow-down. See "Known Issues"
  for what remains outside developer scope.
- **Client-side staleness tick** (`apps/frontend/components/readiness-provider.tsx`): the
  provider now records each poll's `stale_for_s` alongside the client wall-clock receipt time,
  and a separate 1-second interval re-derives a live value between polls
  (`lib/staleness-tick.ts`'s `deriveLiveStaleForS`) so the readiness badge's / preflight
  banner's "as of Ns ago" annotation grows smoothly instead of freezing at the last-polled
  number for up to the full 30s poll-idle interval. `staleForS`'s exposed shape/consumers are
  unchanged — `health-badge.tsx` and `preflight-banner.tsx` needed no edits.
- **Pure tick-derivation helper** (`apps/frontend/lib/staleness-tick.ts`): new export
  `deriveLiveStaleForS(baseStaleForS, receivedAtMs, nowMs)`. Ticking is a deliberate no-op
  (returns the base unchanged) for `null`, `0`, negative, or non-finite bases, so
  `formatStaleAnnotation`'s existing null-rendering guards keep applying to the derived value —
  a fresh/synchronous compute (`0`) or a failed poll (`null`) never starts ticking upward into a
  fabricated number.

## Bug found and fixed during implementation

The first version of the launcher purge (matching the phase spec literally — purge every
`.next-test-*` dir it finds) broke 3 pre-existing tests
(`test_current_build_skips_rebuild`, `test_out_of_band_build_is_treated_as_stale_and_rebuilt`,
`test_launcher_rebuilds_a_bundle_built_for_a_different_backend`) because those tests legitimately
launch the SAME scratch dist dir (matching the reserved `.next-test-*` naming) across multiple
SEQUENTIAL launcher invocations to prove skip-rebuild / out-of-band-detection / backend-mismatch
behavior — the unconditional purge wiped the build each launch treated it as "someone else's
residue" and always forced a rebuild, defeating those tests' entire premise. Fixed by excluding
the current invocation's own `$NEXT_DIST_DIR` from the purge glob (a directory is only "another
process's leftover" if it is NOT the one this launch was told to build into). All three tests
verified passing after the fix, plus the full 14-test module run clean end-to-end (see Tests Run).

## Files Changed

- `incredible_auto_dev/scripts/start-frontend.sh` (= `scripts/start-frontend.sh`, symlinked) --
  residue-purge step (own-dist-dir excluded), loud purge-failure handling. HOST-GUARD block and
  `flock` build-lock byte-unchanged.
- `apps/backend/tests/test_start_frontend_script.py` -- new residue-defense regression test; TC-3
  (`test_broken_source_fails_build_and_leaves_no_stray_process`) now uses a NEW constant
  `_BROKEN_BUILD_SOURCE_REL` (`__tc3_broken_build_source.ts`) instead of the now-auto-purged
  `_BROKEN_SOURCE_REL`, so it still genuinely exercises "the launcher fails on a real broken
  source file" rather than having its fixture silently purged before `next build` runs;
  `_purge_test_residue()` updated to clean up both throwaway names.
- `incredible_auto_dev/scripts/automation/lib/demo_runner.py` (= `scripts/automation/lib/demo_runner.py`,
  symlinked) -- new `_STEP_TIMEOUT_HARD_CEILING_MS` (45000) used by the three per-step timeout
  clamp sites (`_record_steps`, `run_live`, the verify-mode loop); `_default_timeout`'s own
  20000ms ceiling is untouched. Two new self-tests plus a `wait_for_timeouts` spy addition to the
  existing `_FakeLocator` test double.
- `apps/frontend/components/readiness-provider.tsx` -- receipt-time tracking (`staleBaseRef` /
  `staleReceivedAtMsRef`) + a new 1-second tick `useEffect` producing a live `staleForS`.
- `apps/frontend/lib/staleness-tick.ts` -- new pure `deriveLiveStaleForS` export.
- `apps/frontend/lib/staleness-tick.test.ts` -- new unit test file (plain-`node` convention,
  mirrors `lib/staleness-annotation.test.ts`).
- `docs/handoffs/goal-ops-hardening-iter-78-dev.md` -- this handoff.
- `docs/handoffs/goal-ops-hardening-iter-78-frontend.md` -- frontend-focused handoff.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_frontend_script.py -v`
Result: 14 passed, 0 failed (isolated run, no concurrent processes, 739.58s). An earlier run
concurrent with my own manual pre-handoff verification produced 1 spurious failure
(`test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled`, a webpack
`MODULE_NOT_FOUND` from two `next build`s racing for the same `node_modules/.cache`); re-run in
isolation it passed cleanly in 130s, confirming it was contention from my own test process, not a
code defect.

Command: `python3 scripts/automation/lib/demo_runner.py self-test`
Result: 43 passed, 0 failed (includes the 2 new timeout-ceiling tests).

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, no errors (per the environment's own guidance -- never a bare `npx next build`).

Command: `node lib/staleness-tick.test.ts` (documented convention)
Result: could NOT execute locally -- this dev box's Node v22.22.1 was built without TypeScript
type-stripping (`node -p "process.config.variables.node_use_amaro"` -> `false`), the SAME
pre-existing limitation documented in
`docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-dev.md` for
every `lib/*.test.ts` file in this project. Verified the 9 assertions instead by mirroring the
exact function bodies (`deriveLiveStaleForS` + `formatStaleAnnotation`) into a scratch `.mjs` file
and running it under plain `node` -- all 9 passed. The committed `.test.ts` file itself is
unchanged from the project's established convention and will run in the CI/QA Node environment
like every sibling `lib/*.test.ts` file.

## Pre-handoff verification

- Service startup: `scripts/start-backend.sh` then `scripts/start-frontend.sh` (prod mode) on the
  real deterministic ports (8255/3255) -- backend `GET /api/health` answered HTTP 200 in
  0.012-0.049s; frontend served HTTP 200 with the build correctly skipping rebuild ("existing
  '.next' build is current relative to sources — skipping rebuild", Ready in ~330ms). Stopped both
  precisely by port/PID (never a broad `pkill`), restarted both -- no port conflicts, backend
  answered health again immediately, frontend again skipped rebuild and served cleanly. Both
  stopped again at the end; `ss -tlnp` confirms both ports free, no stray `next-server`/`uvicorn`
  processes remain.
- No new external integrations or native dependencies were introduced this iteration -- N/A.
- Frontend tree left pristine: no `__tc3_*` residue files, no `.next-test-*` scratch dirs, no
  uncommitted `tsconfig.json` diff.

## Post-handoff audit fixes (appended by the auditor, 2026-08-13)

Two claims above were amended by the iter-78 audit — see
`docs/handoffs/goal-ops-hardening-iter-78-audit.md` for the full findings:

- **The scratch-dir purge is no longer "unconditional" (audit finding B1).** Excluding only this
  invocation's own `$NEXT_DIST_DIR` left two launcher invocations pointed at DIFFERENT `.next-test-*`
  dirs each treating the OTHER's as abandoned leftover and `rm -rf`-ing it out from under a LIVE
  `next start`. The purge loop now also skips any scratch dir carrying a live `.trendora-serving`
  marker (the same iter-77 marker + PID-reuse cmdline guard `_dist_dir_has_live_server` already
  uses). New regression test:
  `test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving` (PASSED, 43.6s).
  HOST-GUARD and the `flock` build lock remain byte-identical to HEAD (re-verified).
- **The J-09 walkthrough item under "Known Issues" below is now closed (audit finding B2).** The
  raised timeout ceiling was necessary but not sufficient exactly as this handoff predicted; the
  audit set the discriminating `expect` on this iteration's own
  `reports/phase-goal-ops-hardening-iter-78-demo.json` steps 4-5 AND fixed the trigger (the step's
  "one day back" click landed on 2026-07-31, whose evidence was already warm at dataset
  `r2998-f6609160`, so nothing was ever dispatched). Re-recorded: step-04/step-05 now show
  "background compute running (1)" beside "Ready" over a genuinely in-flight compute
  (`/api/health` sampled mid-capture: `asof_key 2026-07-30`, `horizons_done 3/5`).

## Known Issues

- **J-09 walkthrough-capture fix is a necessary-but-not-sufficient engine fix.** The per-iteration
  demo JSON this fix targets (`reports/phase-goal-ops-hardening-iter-78-demo.json`) does not exist
  yet at this pipeline stage -- it is authored later this iteration by demo-narrator, sourced from
  `ui-test-plan.md`/`what-to-click.md` (also not yet generated), not carried forward from iter-77's
  file. The raised timeout ceiling only takes effect on a step that explicitly sets its own
  `timeout_ms` above 20000ms AND targets a discriminating `expect` (e.g.
  `{"target": {"testid": "background-compute-indicator"}}`, not a generic always-present text like
  "Viewing as-of"). If demo-narrator's freshly-authored iter-78 step still captures an idle frame,
  the fix is to set both of those on that specific step in the per-iteration demo JSON once it
  exists (iter-77 precedent: developer directly edited that iteration's own demo.json in a
  fix-mode pass) -- this was NOT something I could pre-seed since demo-narrator overwrites the file
  fresh rather than amending it.
- The `test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled` test is sensitive
  to concurrent `next build` load on this host (see "Bug found and fixed" above for a DIFFERENT,
  now-fixed issue; this note is about test flakiness under contention, not a code defect) --
  passes reliably in isolation; a future CI run that overlaps it with another real build on the
  same host could see a spurious webpack `MODULE_NOT_FOUND`. Not introduced this iteration (the
  test itself is unchanged), just observed directly this round.
- Per the phase spec's binding "Do not redo" list, no change was made to `app.engine.readiness`'s
  server-side cache/staleness/tick logic, `compute_forward_aggregates`, or any
  `journey-scripts/J-*.json` golden.
