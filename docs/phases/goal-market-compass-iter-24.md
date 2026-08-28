# Goal Iteration 24 — Fix the goal-mode launcher's config-context propagation bug

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the fix touches shared launch infrastructure
  (`goal-iter-lean.sh` + `lib/common.sh`/`lib/replay-lane.sh`) reachable from ≥3 independent launch
  call sites (initial browser-QA boot, deterministic-replay restart/retry, review-fix-mode
  re-run / SPEED-2/3 forked boot) whose INTERACTION is exactly what caused iteration 23's
  undetected live incident — a defect five of six pipeline lanes missed, closed only because the
  evaluator cross-referenced WAL-file mtimes against a second app's log. No single journey's test
  suite covers this interaction; it needs independent review and audit.
- **Frontend Present:** no
- **Target journeys:** none — this iteration is an owner-authorized Goal Mode harness/tooling fix
  with zero journey-visible product change (see NOTES and the assumption-ledger entry
  "Target journeys = none for an owner-authorized harness-safety fix"). Regression coverage
  substitutes for a target-journey browser-qa pass; see Required-still-passing and TESTING
  REQUIREMENTS below.
- **Required-still-passing journeys:** J-01, J-04, J-10 (the entire currently-passing set minus
  J-11, which stays CLOSED per "Do not redo" and owner ruling item 1 — do not re-verify it)
- **Anti-goal reminders:**
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed /
    local provider fixtures — no live external network calls or paid data services without an
    explicit goal.md amendment. *(critical)*
  - Owner ruling (2026-08-27, "OWNER RULING — J-11 database recovery accepted", item 3) also binds
    this iteration though it is not a numbered anti-goal: *"The canonical repaired database stays
    OFF and must not be mutated by this verification."* The fix's own regression test must prove
    it never boots or writes to `apps/backend/data/trendora.db`.

## GOAL

Close the exact defect that let iteration 23's deterministic-replay/retry path silently boot the
protected canonical database instead of the disposable clone it was told to use, so every future
goal-mode iteration's browser-QA, replay, retry, and restart launches reliably honor whatever
backend-launch override the iteration supplied — or fail closed before ever spawning a backend.

## BACKGROUND

Iteration 23 closed J-11 (disposable-clone serving verification PASSED) but, in the same run, its
deterministic-replay lane silently booted the real `apps/backend/data/trendora.db` and wrote 10
cache rows into it — proven by the evaluator matching the app's log timestamp to the database's
`-wal` file mtime to the millisecond (iter-23 eval; lesson iter-23b: a `.db` sha256 alone cannot
detect a WAL-mode write). The session STALLED, asking the owner three questions. A now-uncommitted
addition to `docs/goal.md` (inside the J-11 section, following the existing "accept J-11 D-G
database recovery" ruling) answers all three:

1. J-11 stays CLOSED/PASSING — do not reopen.
2. The 10 resulting cache rows are accepted in place — no cleanup writes.
3. **Exactly one narrow tooling fix is authorized**: `goal-iter-lean.sh` must make every browser-QA,
   deterministic-replay, retry, and restart backend launch preserve the SAME
   `TRENDORA_CONFIG`/`CHAIN_START_BACKEND_CMD` context the iteration originally supplied, must never
   silently fall back to the plain canonical-DB launch once an override is in force, must fail
   closed before boot when required context is missing, and must ship a focused regression test
   reproducing the iteration-23 failure. No broader Goal Mode redesign is authorized.
4. The iter-23 disposable clone (`runs/goal-market-compass-iter-23/verify-clone/`) may be deleted
   once this fix is verified — not required this iteration.
5. Normal Market Compass product work resumes immediately once this fix lands and is verified — no
   further owner authorization needed.
6. Owner continuation policy: do not STALL for reversible cleanup; only raw/canonical data repair,
   immutable-manifest mutation, schema migration, new network access, or another genuinely
   irreversible decision needs the owner.

This directly resolves the `Active blockers: HUMAN — owner decision required` line in the inlined
iteration-state digest — that blocker is now answered, and this iteration executes the one item it
authorized. Two lessons from this session apply directly: (iter-22b) a check gating an irreversible
action must mutate the REAL production module and prove the suite fails first, never a hand-built
fixture; (iter-23b) any "database unmutated" claim must bracket `.db` + `-wal` + `-shm`, captured
AFTER the last lane finishes, not a bare `.db` sha256. Both must shape this iteration's own
regression-test and no-canonical-write proof. The repo also carries a byte-identical vendored
mirror of the buggy script at `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` (the path
the owner ruling names); see the assumption-ledger entry — both copies get the identical patch so
the fix actually takes effect on the live path this project executes, not only the mirror.

Depth is **full** against a `full` binding evaluator recommendation for this iteration — no escape
condition is needed since the recommendation itself is full, but a numbered trigger is cited per
this agent's self-check: Trigger 1 (structural/cross-cutting), justified above. This is also the
FOURTH time in this session (after iters 2, 6, 8, and 23 itself) that a `Depth: full` spec would
matter for exactly this kind of shared-launch-infrastructure risk; iter-23's own "Do not redo" list
explicitly flags "Spec depth was full, dispatch ran lean — request full." This spec requests full
depth be honored, not silently demoted.

Priority-rubric note: none of J-02/J-03/J-05/J-06/J-07/J-08/J-09 (the remaining partial/failing
journeys) is targeted this iteration — the owner's newest, most specific ruling designates the
launcher fix as the mandatory next step ahead of all normal product work (ruling items 3 and 5),
which outranks the general journey-selection rubric for this one iteration. Normal journey work
(J-09 first, per the goal file's own suggested build order) resumes next iteration once this fix is
verified.

## IN SCOPE

### Backend (Goal Mode harness/automation only — no Trendora application code)
- [ ] In `scripts/automation/goal-iter-lean.sh` (and its identical vendored mirror
  `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` — apply the same patch to both, see
  BACKGROUND/assumption-ledger), audit every place a backend gets (re)started in a lean iteration
  run — the initial `run_browser_qa_boot_and_replay` boot, the SPEED-2/SPEED-3 forked
  browser-qa/replay boot, the review-fix-mode re-run, and the deterministic-replay lane's REL-5
  restart-after-mid-run-failure and REL-14 preflight-retry paths (`scripts/automation/lib/common.sh`,
  `scripts/automation/lib/replay-lane.sh`) — and make each one resolve its backend-launch command
  from the SAME `CHAIN_START_BACKEND_CMD`/override context the iteration originally established,
  never independently re-deriving the bare `bash scripts/start-backend.sh` default once an override
  was set for that run.
- [ ] Where a launch point's calling context requires an override to already be present (e.g. a
  disposable-clone verification run) and finds it missing/empty, fail closed with a clear error
  BEFORE spawning any backend process — never boot the bare default silently.
- [ ] Add one focused regression test reproducing the exact iteration-23 sequence (initial boot
  with an off-canonical override, then the deterministic-replay restart/retry code path) that FAILS
  against the pre-fix code and PASSES against the fixed code, per iter-22b's lesson: mutate/exercise
  the REAL `goal-iter-lean.sh`/`common.sh`/`replay-lane.sh` code paths, not a hand-built fixture.
- [ ] The test itself must never boot against or write to the real `apps/backend/data/trendora.db`
  — target a disposable stub/fixture backend command (reuse the existing, already-tested
  `scripts/start-backend-j11-verify.sh` / `app/engine/j11_disposable_clone.py` tooling per the "Do
  not redo — reuse it" instruction, or an equivalently inert stub start command for a pure
  launch-context unit test).

### Frontend
- None. No UI, page, or endpoint changes.

### New user-facing capability
None — this iteration changes only the goal-mode automation harness that runs between iterations;
it introduces no Trendora product capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — `apps/frontend/`, `apps/backend/app/` (API/engine/models) are untouched; only
`scripts/automation/goal-iter-lean.sh`, its sourced libs, and their test coverage change.

### Blueprint conformance
No new surfaces — this iteration adds no page and touches no Information-Architecture home.
`runs/goal-session-market-compass/state/blueprint.md` is unchanged.

### Data-contract additions
None. No new displayed value; no new computing module; no new serving endpoint.

## OUT OF SCOPE

- The 10 accepted derived-cache rows already in the canonical database — do NOT delete, rewrite, or
  otherwise touch them (owner ruling item 2, binding: "Do not perform cleanup writes").
- Reopening J-11 recovery, Stages D–G, or the serving/replay verification — CLOSED; do not redo
  (owner ruling item 1; iteration-state "Do not redo" list).
- Any broader Goal Mode / stall-detector / depth-system redesign, or unrelated automation cleanup
  (owner ruling item 3's explicit exclusion).
- Deleting the iter-23 disposable clone at `runs/goal-market-compass-iter-23/verify-clone/` —
  permitted once the fix is verified (owner ruling item 4) but not required this iteration; may be
  picked up as a trivial follow-up once verification evidence exists.
- Any Trendora product journey work — J-02, J-03, J-05, J-06, J-07, J-08, J-09 all stay exactly as
  recorded; normal product work resumes next iteration per owner ruling item 5.
- Any live/canonical-database boot with an alternate config override during this iteration's own
  test development — the fix must be proven with disposable/stub tooling only.
- Any change to `apps/backend/app/` or `apps/frontend/app/` — this iteration is automation-only.

## DEFINITION OF DONE

- [ ] Every backend-launch call site reachable from a lean iteration run (initial boot, forked
  boot, review-fix-mode re-run, deterministic-replay restart, preflight retry) preserves a
  supplied `CHAIN_START_BACKEND_CMD`/`TRENDORA_CONFIG` override identically across all of them
  (TC-1, TC-2, TC-3)
- [ ] A missing-but-expected override fails closed before any backend boot (TC-4)
- [ ] The new regression test reproduces the iteration-23 defect against pre-fix code and passes
  against fixed code (TC-5, TC-6)
- [ ] The regression test itself never boots or writes to the real canonical database, proven by a
  `.db`+`-wal`+`-shm` state comparison captured after the test run completes (TC-9, applying the
  iter-23b lesson)
- [ ] Required-still-passing journeys J-01, J-04, J-10 remain green via deterministic replay (no
  override supplied — the normal, unaffected path) (TC-7)
- [ ] No anti-goal violation introduced; AG-9 holds (no live network calls anywhere in the new test
  or fix) (TC-9)
- [ ] Unit tests pass; no regressions in the existing `scripts/automation` test coverage
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-24-dev.md`, citing the exact
  pre-fix/post-fix test commands and their pass/fail outcomes, and confirming both copies of
  `goal-iter-lean.sh` received the identical patch

## TESTING REQUIREMENTS

- Browser: none required — no target journey this iteration. Required-still-passing regression
  (J-01, J-04, J-10) runs via deterministic replay only; no new LLM browser-qa dispatch is needed
  since none of the three journeys' surfaces changed.
- Unit/integration: the new focused regression test named in IN SCOPE, plus any existing
  `scripts/automation` shell/pytest coverage that already exercises `ensure_services_running` /
  the replay-lane restart path — confirm those still pass unmodified.
- Error cases: a launch point that expects an override and finds none must error/exit non-zero
  before spawning a backend process — never proceed with a silent default.

Test-first contract:

- TC-1: given `CHAIN_START_BACKEND_CMD` is set to a disposable-clone command for an iteration's
  initial browser-QA boot, when the deterministic-replay lane's REL-5 restart-after-failure path
  re-invokes `ensure_services_running`, then the backend is (re)started with that exact same
  command string — not the bare `bash scripts/start-backend.sh` default.
- TC-2: given the same override is set, when the SPEED-2/SPEED-3 forked browser-qa+replay boot (or
  the review-fix-mode re-run of `run_browser_qa_boot_and_replay`) executes in its own
  subshell/child process, then that child's resolved `BACKEND_START_CMD` is byte-identical to the
  parent's, not recomputed from an unset `CHAIN_START_BACKEND_CMD`.
- TC-3: given an override is set for an iteration's first backend boot, when any additional
  backend (re)start happens later in the same iteration run (crash restart, timeout retry), then a
  stored/logged comparison of the first and later launch commands shows zero mismatch.
- TC-4: given a launch point's calling context expects an override to be present but finds it
  empty/unset at invocation time, when that launch point executes, then the script exits non-zero
  with an explicit error message before any backend process is spawned, and no backend log file is
  created for that attempt.
- TC-5: given the pre-fix `goal-iter-lean.sh`/`common.sh`/`replay-lane.sh` code (this iteration's
  diff reverted), when the new regression test runs the simulated initial-boot-then-restart
  sequence, then the test FAILS, demonstrating it reproduces the iteration-23 defect.
- TC-6: given the fixed code, when the same regression test runs, then it PASSES and the observed
  restart command string equals the original override string exactly.
- TC-7: given no override is supplied (the normal case for ordinary journey re-verification), when
  the lean iteration's deterministic-replay lane runs the J-01/J-04/J-10 golden scripts, then all
  three replay PASS exactly as before this fix — the unset-override path is unchanged.
- TC-8: given the fix lands, when the developer's targeted test command for the new regression test
  is run, then it reports 0 failures and the dev handoff cites the exact command and result.
- TC-9: given the new regression test suite has just finished running, when the developer captures
  `apps/backend/data/trendora.db`, `trendora.db-wal`, and `trendora.db-shm` mtimes/sizes (or a
  content hash) immediately before and immediately after the test run, then all three files are
  byte-identical/unchanged — proving the fix's own verification never touched the canonical
  database.

## NOTES

- This spec's Target journeys is intentionally empty; see the assumption-ledger entries
  "which copy of `goal-iter-lean.sh`..." and "Target journeys = none for an owner-authorized
  harness-safety fix..." (`runs/goal-session-market-compass/state/assumptions.md`, iter-24) for the
  interpretation calls behind that and the dual-file fix scope.
- `CHAIN_MAINTENANCE_ISOLATION` and `CHAIN_REQUIRE_FULL_DEPTH` are both confirmed unset in this
  environment — per standing session guidance, do NOT re-arm either; nothing in this spec requires
  them (the regression test targets a disposable/stub backend, not the canonical one, so
  maintenance isolation is unnecessary here).
- Next iteration (iter-25), once this fix is verified: resume normal Market Compass product work
  starting with **J-09** (host resource-fit — small, config-value + measurement only), per the goal
  file's own suggested build order and the carried-forward evaluator recommendation, then
  J-05/J-06, then J-07/J-08.
- Non-blocking items carried forward from iter-23's eval, not addressed here (owner ruling item 6
  says do not STALL for these): re-pointing four trap citations (auditor B2), two asserted-not-measured
  traps, ten pre-existing unrelated `test_data_manager.py` failures, one static-audit false positive,
  and J-04's screenshot recapture on the next real browser-qa run.
- If the developer's investigation finds the launch-context loss happens somewhere outside the
  five call sites named above (e.g. inside `lib/quota-retry.sh`'s pre-hook), it is still in scope —
  the owner ruling's bound is functional ("every browser-QA, deterministic-replay, retry and
  restart backend launch"), not a literal file list.
