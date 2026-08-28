# Goal Iteration 25 — J-09 host-fit re-measurement + regression-replay parser fix

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 25
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (mandatory, no exceptions per the depth rubric).
- **Frontend Present:** no
- **Target journeys:** J-09 — "The backend fits the host" (host resource-fit re-measurement; its config change already landed at iter-4, this iteration re-verifies against the CURRENT live database state and records the result honestly, per its own acceptance text).
- **Required-still-passing journeys:** J-01, J-04, J-10 — re-verify for real via deterministic replay (skipped, no-fault, at iter-24 by a parser bug this iteration's own scope fixes).
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider
    fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be
    launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps)
    plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken, or bypass
    these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test
    outcomes. The ceiling VALUES are an owner-set envelope (current: `memory_cap_mb` 8192,
    `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in
    `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*
  - Loop-mechanics rule (`docs/goal.md`, 2026-08-21, binding though not a numbered anti-goal): *"`Depth: full`
    must never silently become `lean`... inability to run the required full-depth lanes MUST be surfaced
    explicitly and MUST NOT silently fall back to `lean`."* This spec's `Depth: full` traces to a mandatory
    ESCALATE trigger; see BACKGROUND for why enforcement is a live concern this iteration.
  - Owner ruling (`docs/goal.md`, "OWNER RULING — J-11 CLOSED", 2026-08-27): item 5 authorizes normal product
    work with no further permission; item 6 forbids stalling merely for reversible/disposable cleanup; item 2
    forbids cleanup writes to the ten accepted iteration-23 cache rows — this iteration touches none of them.

## GOAL

Get a fresh, dated, honest read on whether the standing-warm backend memory footprint still fits this
shared host after everything that has changed since iter-4's cache_size reduction, and close the
regression-replay parsing defect that silently emptied the required-still-passing re-test list, so
J-01/J-04/J-10 are genuinely re-verified this iteration instead of merely assumed.

## BACKGROUND

J-09's `cache_size` change (`config.yaml` `database.pragmas.cache_size` `-262144` → `-65536`) and its
first standing-warm measurement, concurrent-load check, and byte-identity spot check all landed at
iter-4 (`reports/perf-budgets.md` Addenda 39/40) — an HONEST MISS: 3,439,100 kB measured against the
≤ 2,621,440 kB (2.5 GB) target, a real 28.9% reduction but still over. Per J-09's own acceptance text
("if the target is missed, record the honest measured figure and stop for owner review — never widen
the target to pass"), that iteration correctly stopped there. Since then the canonical database has
gone through J-10's raw recovery and J-11's full Stage D→G derived-state regeneration — materially
different content and likely a different derived-cache footprint than iter-4 measured against. This
iteration re-runs J-09's own steps 2-5 (no config edit — `cache_size` stays `-65536`, `pool_size` and
`max_overflow` stay untouched per J-09's explicit prohibition) against the CURRENT live state, and
appends a NEW dated addendum beside (never overwriting) the iter-4 figures. Whichever way the number
lands, this is recorded honestly; a repeat miss is J-09's own anticipated non-blocking outcome, not a
new blocker (one of the "FIVE OLDER OWNER QUESTIONS" in the iteration-state digest — whether 3.44 GB
was acceptable — stays open either way and is not this iteration's call to resolve).

Separately, the iter-24 evaluator (ESCALATE) found that `replay_lane_spec_journeys`
(`scripts/automation/lib/replay-lane.sh:75-77`, real path
`incredible_auto_dev/scripts/automation/lib/replay-lane.sh` — `scripts/` is a tracked symlink into
`incredible_auto_dev/`, so there is exactly one file to patch) takes the FIRST line matching a label
regex, with no check that the line actually contains a `J-NN` token. Iter-24's own spec tripped this:
its `Target journeys:` bullet's prose mentioned the phrase "Required-still-passing" one line before the
real `**Required-still-passing journeys:**` bullet, so the parser matched the prose line first, returned
an empty set, and J-01/J-04/J-10 went unverified with only a benign-looking "replay: no" logged — no
error, no lane noticing. This spec's own metadata section is written to avoid that exact trap (the
`Required-still-passing journeys:` label appears nowhere in prose before its own bullet, and that bullet
is one unbroken physical line). This iteration's own IN SCOPE additionally fixes the underlying parser
so a future spec cannot repeat the same silent failure, and adds a check so a declared non-empty journey
set that parses to zero is reported as a lane warning, not swallowed.

**Depth.** Prior verdict was ESCALATE, so full depth is mandatory (rubric Trigger 3, no exceptions) —
independent of the dispatch's own binding `full` recommendation. This is also the THIRD consecutive
iteration (23, 24, 25) where `Depth: full` is the correct call and the FIFTH time this session a `full`
spec has been demoted to `lean` by the arbiter's cost rung ("reason: full-cap") per the inlined
iteration-state digest — twice in a row (iters 23, 24) with no independent auditor dispatched either
time. Per this agent's own governing instructions, the operator-only `Depth enforcement: required` line
is NOT something this agent may self-grant (doing so is exactly the self-justifying-governor-bypass
anti-pattern the instructions name) — so it is deliberately NOT included below. If the operator wants
this iteration's full depth to be a hard requirement rather than an arbiter-demotable recommendation,
that line is theirs to add; per standing session guidance, `CHAIN_REQUIRE_FULL_DEPTH` and
`CHAIN_MAINTENANCE_ISOLATION` stay OFF and are not being requested here.

**Priority-rubric note.** J-09 is the smallest available unit of real product work (rubric rule 4) and
is the goal file's own explicit next-in-queue item (Loop mechanics: "J-09 jumps the queue — build it as
the NEXT slice"); the parser fix is a low-risk, non-journey harness fix bundled in per the iter-24
evaluator's own explicit next-step recommendation ("FIX THE PLAN-READING BUG... in the same round").
Neither is a "risky" journey in the rubric's sense (no data-model change, no provider integration, no
cross-cutting product refactor), so bundling them does not violate "never bundle two risky journeys."
No regressed journey exists to prioritize ahead of this (iteration-state: 0 regressed). J-11 is CLOSED
per the "Do not redo" list and is not touched, re-tested, or re-planned here.

## IN SCOPE

### Backend (Trendora measurement only — zero application code change; Goal-mode harness fix separately)
- [ ] Re-run J-09's standing-warm memory measurement (goal.md J-09 step 2's methodology, replicated at
  Addendum 40) against the CURRENT live backend + database, started via `scripts/start-backend.sh` with
  `config.yaml`'s `cache_size` unchanged at `-65536` and `pool_size`/`max_overflow` untouched; sample
  `/proc/<pid>/status` VmPeak at the plateau of the same lighter concurrent-burst path (no
  `backfill`/`rebuild` job, no throwaway DB copy).
- [ ] Append a NEW dated addendum to `reports/perf-budgets.md`, beside (never replacing) Addenda 39/40,
  recording the fresh VmPeak figure and its comparison against both the ≤ 2,621,440 kB (2.5 GB) target
  and the iter-4 figure (3,439,100 kB).
- [ ] Re-run the concurrent-load burst check (iter-4's methodology / `test_data_manager_concurrency_load.py`)
  against the current backend; record the total request count and confirm zero `QueuePool` TimeoutError.
- [ ] Re-run the byte-identity spot check on `GET /api/dashboard`, `GET /api/stocks`,
  `GET /api/market-phase`, `GET /api/compass`, all at `as_of=2026-08-10`, against the current backend;
  record each response's md5 in the dev handoff (AG-3 correctness — no config edit happens this
  iteration, so this proves the current served values are exactly what the canonical stored rows for
  that as-of produce, not a before/after diff).
- [ ] If the fresh VmPeak figure still exceeds the 2.5 GB target: record it honestly, do NOT widen the
  target, and do NOT touch `pool_size`/`max_overflow`/any AG-10 owner-only cap value — this is J-09's
  own anticipated outcome per its acceptance text, not a new blocker for this iteration.

### Backend (Goal Mode harness/automation only — no Trendora application code)
- [ ] Fix `replay_lane_spec_journeys` in `scripts/automation/lib/replay-lane.sh` (patch the one real
  file at `incredible_auto_dev/scripts/automation/lib/replay-lane.sh`; `scripts/` is a tracked symlink
  — never patch both) so that, given a label, it selects the line that actually contains one or more
  `J-NN` tokens for that label rather than unconditionally taking the first regex-matching line — a
  label phrase appearing earlier in unrelated prose must never silently empty the parsed set.
- [ ] Add a check (in `goal-iter-lean.sh` and `browser-qa-phase.sh`, both call sites of
  `replay_lane_spec_journeys`) so that a spec containing a non-empty declared journey-set bullet that
  still parses to zero `J-NN` tokens is reported as an explicit lane WARNING/error line — never logged
  only as a bare "replay: no" indistinguishable from "nothing to replay."
- [ ] Add one focused regression test that reproduces iter-24's exact failure mode (a spec file whose
  `Required-still-passing` label phrase appears in prose before its own bullet) against the pre-fix
  parser and proves it now returns the correct non-empty set post-fix.
- [ ] Delete the now-authorized-for-removal disposable clone at
  `runs/goal-market-compass-iter-23/verify-clone/` (owner ruling item 4 — the launcher fix it existed
  to verify is landed and confirmed; ~7.8 GB) — first confirm
  `tests/automation/test-backend-launch-context.sh` still reports 18/18 passed with the clone absent
  (proving nothing depends on its presence), then delete and record the freed space in the dev handoff.

### Frontend
- None. J-09's own acceptance text waives its walkthrough ("deliberately backend-only — no UI surface
  changes"); the parser fix is automation-only.

### New user-facing capability
None this iteration.

### New information displayed
None — J-09 produces a new dated measurement line in `reports/perf-budgets.md`, an internal ops report,
not a UI-displayed value.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — `apps/frontend/` is untouched; `apps/backend/app/` gets zero code changes (measurement only, no
config/code edit); only `reports/perf-budgets.md` (new addendum), `scripts/automation/lib/replay-lane.sh`
+ its callers + its new regression test, and the deleted iter-23 clone directory change.

### Blueprint conformance
No new surfaces — this iteration adds no page and touches no Information-Architecture home.
`runs/goal-session-market-compass/state/blueprint.md` gets an informational append-only note only
(no IA or Data Contract row edit), matching the pattern of every prior no-surface iteration in this
session.

### Data-contract additions
None. No new displayed value; no new computing module; no new serving endpoint.

## OUT OF SCOPE

- Touching `database.pragmas.cache_size`, `pool_size`, `max_overflow`, or any other config value — this
  iteration is measurement-only; J-09's own steps authorize exactly one config edit and it already
  landed at iter-4.
- Widening the 2.5 GB target, or treating a repeat honest miss as a failure requiring a fix this
  iteration — J-09's acceptance text explicitly anticipates and accepts this outcome.
- `_BarCache.prefill`'s cold-path re-bound (Constraints item (c)) — explicitly NOT part of J-09; rides a
  future applicable slice per the goal file's own framing.
- Any Trendora product journey other than J-09 — J-02, J-03, J-05, J-06, J-07, J-08 stay exactly as
  recorded; J-11 is CLOSED and not reopened, re-tested, or re-planned (owner ruling item 1; "Do not
  redo" list).
- The ten accepted iteration-23 cache rows already in the canonical database — do NOT delete, rewrite,
  or otherwise touch them (owner ruling item 2).
- Any broader Goal Mode / stall-detector / depth-system redesign beyond the one named parser defect —
  the fix is scoped exactly to `replay_lane_spec_journeys`'s label-matching logic and its silent-empty
  reporting gap, nothing more.
- Any live/canonical-database boot with an alternate config override — normal work has resumed (owner
  ruling item 5); no isolation/clone mechanism is needed or used this iteration.

## DEFINITION OF DONE

- [ ] J-09 fresh, dated VmPeak re-measurement appended to `reports/perf-budgets.md`, with an explicit
  comparison against both the 2.5 GB target and the iter-4 figure (TC-1)
- [ ] Concurrent-load burst check re-run clean, zero `QueuePool` TimeoutError, recorded in the dev
  handoff (TC-2)
- [ ] Byte-identity spot check clean across all 4 endpoints at `as_of=2026-08-10`, md5s recorded (TC-3)
- [ ] `replay_lane_spec_journeys` no longer returns an empty set when a label phrase appears in prose
  before its own bullet (TC-4, TC-5)
- [ ] A non-empty declared journey set parsing to zero is now reported as an explicit warning, not
  silent (TC-6)
- [ ] Required-still-passing journeys J-01, J-04, J-10 remain green via this iteration's own (fixed)
  deterministic-replay lane, with `reports/phase-goal-market-compass-iter-25-regression-replay-results.md`
  produced and showing PASS for all three (TC-7)
- [ ] iteration-23 disposable clone deleted only after confirming the launcher-fix test suite still
  passes 18/18 without it; freed space recorded (TC-8)
- [ ] No anti-goal violation introduced; AG-9 holds (zero live network calls this iteration); AG-10
  host-guard/pool config values byte-unchanged (`git diff` shows only the new perf-budgets addendum and
  the replay-lane.sh/test files)
- [ ] Unit tests pass; no regressions in existing `scripts/automation` and `apps/backend/tests` coverage
  this iteration's changes touch
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-25-dev.md`

## TESTING REQUIREMENTS

- Browser: none required for the target journey — J-09's walkthrough is explicitly waived
  (backend-only). Required-still-passing regression (J-01, J-04, J-10) runs via deterministic replay;
  dispatch an LLM browser-qa fallback only if the replay lane reports FAIL or SKIPPED-INFRA for any of
  the three.
- Unit/integration: the new `replay_lane_spec_journeys` regression test named in IN SCOPE; the existing
  `test_data_manager_concurrency_load.py` targeted subset; existing `scripts/automation` shell/pytest
  coverage touching `ensure_services_running` / the replay-lane restart path, confirmed still passing
  unmodified.
- Error cases: a spec with a non-empty declared journey-set bullet that parses to zero `J-NN` tokens
  must produce a visible warning/error line from the lane, never a silent empty result.

Test-first contract:

- TC-1: given the backend is started via `scripts/start-backend.sh` against the current live database
  with `config.yaml`'s `cache_size` unchanged at `-65536`, when the same lighter concurrent-burst
  standing-warm methodology from Addendum 40 is re-run and `/proc/<pid>/status` VmPeak is sampled at the
  plateau, then a new dated addendum line is appended to `reports/perf-budgets.md` (Addenda 39/40
  untouched) reporting the measured VmPeak in kB with its delta vs 2,621,440 kB and vs 3,439,100 kB.
- TC-2: given the same backend, when a request burst approaching `server.limit_concurrency` (64)
  simultaneous in-flight connections is issued, then zero `QueuePool` TimeoutError occurs and the total
  request/error counts are cited in the dev handoff.
- TC-3: given the same backend, when `GET /api/dashboard`, `GET /api/stocks`, `GET /api/market-phase`,
  and `GET /api/compass` are each requested at `as_of=2026-08-10`, then each response body's md5 is
  recorded in the dev handoff and matches what the canonical stored rows for that as-of produce.
- TC-4: given the pre-fix `replay_lane_spec_journeys` function and a spec file whose
  `Required-still-passing` label phrase appears in prose on a line preceding the real
  `**Required-still-passing journeys:**` bullet (reproducing iter-24's own spec structure), when the
  function parses that file for the `Required-still-passing` label, then it returns an EMPTY journey
  string.
- TC-5: given the FIXED function and the identical reproduction spec file, when the function parses it
  for the same label, then it returns the correct non-empty set (`J-01 J-04 J-10`), sourced from the
  real bullet, not the prose mention.
- TC-6: given a spec whose declared journey-set bullet is non-empty but parses to zero `J-NN` tokens
  (e.g., malformed IDs), when the lane runs, then it emits an explicit WARNING/error line distinct from
  the ordinary "replay: no" no-work message, asserted by the new regression test.
- TC-7: given this iteration's own spec (`docs/phases/goal-market-compass-iter-25.md`, whose
  `Required-still-passing journeys:` bullet is one unbroken physical line with no earlier prose mention
  of the label), when the deterministic-replay lane runs, then
  `reports/phase-goal-market-compass-iter-25-regression-replay-results.md` is created and shows PASS for
  J-01, J-04, and J-10, and the run log shows a non-empty `REQUIRED_JOURNEYS`.
- TC-8: given `tests/automation/test-backend-launch-context.sh` reports 18/18 passed with the iter-23
  clone directory present, when the clone at `runs/goal-market-compass-iter-23/verify-clone/` is deleted
  and the same test suite is re-run, then it still reports 18/18 passed (no hidden dependency on that
  artifact) and the freed disk space (~7.8 GB) is recorded in the dev handoff.

## NOTES

- This spec deliberately keeps its `Target journeys:` and `Required-still-passing journeys:` metadata
  bullets each on one unbroken physical line, with neither label phrase appearing anywhere earlier in
  prose, specifically to avoid reproducing the iter-24 parser defect this iteration's own IN SCOPE
  fixes. Any future edit to this spec must preserve that property.
- Per this agent's own governing instructions, `Depth enforcement: required` and
  `Maintenance isolation: required` are deliberately NOT set anywhere in this spec — those are
  operator-only lines, and self-granting either here would be the exact governor-bypass anti-pattern the
  instructions name. If the operator wants this iteration's full depth to be non-demotable given the
  three-strikes full-cap history described in BACKGROUND, that is theirs to add (or to set
  `CHAIN_REQUIRE_FULL_DEPTH` for this run) — not this agent's call.
- An assumption-ledger entry (`runs/goal-session-market-compass/state/assumptions.md`, iter-25) records
  the interpretation call behind re-measuring J-09 now rather than treating it as fully discharged /
  owner-blocked after its iter-4 honest miss.
- Non-blocking items carried forward, not addressed here (owner ruling item 6 — do not stall for these):
  J-04's screenshot recapture to include the candidate card; the J-02/J-03 repaired-state replay named
  in J-11's own acceptance text; whether 3.44 GB (or this iteration's fresh figure) is ultimately
  acceptable for J-09; J-06's "underlying run unavailable" wording; J-01's first two test-step wording;
  whether an empty "next-session focus" is acceptable; whether MNST joins the recovery list;
  `goal_gate.py`'s duplicate-journey-heading defect (must close before any GOAL_ACHIEVED certification).
- Next iteration, once this one's evidence lands: continue normal product work per the goal file's
  suggested order — J-05/J-06 (freeze/integrity pair), then J-07/J-08 (surface pair), unless J-09's
  fresh measurement or the owner's read of it changes the order.
