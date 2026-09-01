# Goal Iteration 34 — J-09 closing re-measurement (independent, ≥6-min quiet host) + results-file evidence-recording fix, at genuine full depth

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 34
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (mandatory, no exceptions per the depth rubric).
  This iteration's own evaluator depth recommendation is also `full` and binding; the ESCALATE
  trigger governs independent of that recommendation.
- **Frontend Present:** no
- **Target journeys:** J-09 — "The backend fits the host" — **confirmation only**, per the binding
  "Do not redo" carried from iter-33: the memory-bound mechanism (`warmup.py:351`,
  `startup.warmup_bar_cache_bounded`) shipped and is CLOSED; this iteration re-measures and fixes
  how its evidence is recorded, it does not rebuild anything.
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10, J-11
  (full regression widening — this is the session-closing confirmation round; every other passing
  journey is re-verified before any GOAL_ACHIEVED recommendation becomes possible).
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be
    launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps)
    plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken, or bypass
    these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test
    outcomes. The ceiling VALUES are an owner-set envelope (current: `memory_cap_mb` 8192,
    `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in
    `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **`Depth: full` must never silently become `lean` (owner, 2026-08-21).** This session has had an
    explicit `Depth: full` spec dispatched as `lean` three times (iters 2, 6, 8) — including iteration
    8, the one that performed the first real writes to the production database, and including
    iteration 6, where the demotion also let an ungated browser-QA replay run against the damaged
    dataset. That is not acceptable for a recovery path whose correctness depends on adversarial
    review and audit. **When the goal or an iteration spec requires `Depth: full`, inability to run the
    required full-depth lanes MUST be surfaced explicitly and MUST NOT silently fall back to `lean`.**
    For any J-10 iteration that can write recovery data, the intended full audit/review depth is
    required before the iteration may be treated as fully accepted. If the infrastructure cannot
    provide `full`: mark the depth requirement **unmet**, preserve the implementation and recovery
    evidence, do **not** pretend `lean == full`, and surface it for owner/evaluator decision. Never
    fabricate an audit result to satisfy this. Do **not** re-run destructive or network actions merely
    to obtain another depth marker, unless the existing idempotent recovery design makes that provably
    safe and this goal explicitly allows it.

## GOAL

Deliver the honest, independently-corroborated closing measurement of J-09 (extended window, quiet
host) and fix the goal-mode harness so a walkthrough-waived target journey's non-UI evidence can be
recorded without mechanically blocking `GOAL_ACHIEVED` — while genuinely running (and disclosing) the
full-depth pipeline that iter-33 silently skipped.

## BACKGROUND

All eleven Must-have journeys are `passing` as of iter-33, and the binding "Do not redo" list forbids
rebuilding J-09's mechanism — there is no new product surface to build this cycle. iter-33 nonetheless
returned **ESCALATE** for two independent, non-product reasons the evaluator verified directly: (1) the
spec required `Depth: full` under a written Trigger-1 justification and `session.json` recorded
`next_depth: "full"`, yet `iter-33/depth-dispatched` reads `lean` with no auditor/QA/closure/ux-regression
step and no disclosure anywhere — a direct violation of the binding loop-mechanics rule quoted above; and
(2) `goal_gate.py results` already exits 1 on iter-33's own merged results file because J-09 — whose
`docs/goal.md` Acceptance text reads verbatim "**Walkthrough:** waived — deliberately backend-only (no UI
surface changes); the demo requirement is replaced by the dated VmPeak measurement and drill citations in
the dev handoff" — has no browser row and is therefore listed under "Missing Target Journeys", forcing the
merged headline to `BLOCKED`. Per this framework's rule ("prior verdict ESCALATE ⇒ this iteration MUST run
`full`, no exceptions"), depth here is non-negotiable, independent of the evaluator's own binding
recommendation which also reads `full`.

Per the priority rubric: no journey is regressed (rule 1); the last `coherence.md` was `COHERENCE-PASS`,
so no consolidation-only pass is forced (rule 2); this is the smallest available unit that unblocks
`GOAL_ACHIEVED` for the whole session (rule 3/4) and touches exactly one already-closed journey's
evidence trail plus one harness fix — not two risky product changes (rule 5); nothing here is
human-blocked (rule 6, confirmed by iter-32's own lesson that "owner-authored" Constraints (b)/(c) are
build items, not permission-waits) — this iteration is deliberately real engineering (an extended
independent measurement plus a merge/gate code fix), not evidence-only (rule 7's exception does not
apply, since item (3) below is a genuine code change).

**Lessons applied.** iter-32: a monotonic VmPeak figure alone never tells you what a process holds —
plot the neighbouring `VmSize_kB`/`VmRSS_kB` columns before concluding anything (applied below: both
columns are sampled and reported at the plateau, not just the peak). iter-33 (window-length lesson): a
measurement's WINDOW LENGTH is itself a variable — iter-33's 180s window stopped before iter-32's
observed t+181 release point, inventing an apparent regression; this iteration samples **≥360 seconds**
per the prior evaluator's own explicit instruction. iter-33 (representation-switch lesson): the memory
win is a representation change tied to the data basis, not a size cap — a corollary risk to watch for,
not something to re-engineer this round (binding "Do not redo"). iter-29/30/31 (golden-hygiene family):
a lesson bound to the TARGET journey does not automatically protect REQUIRED-STILL-PASSING journeys —
this spec's golden-hygiene check below is scoped to all ten required journeys, not just J-09. iter-32
(third lesson): "a gate that asserts an artifact without opening it is indistinguishable from a gate
that read it" — the dev handoff must record the *observed* `goal_gate.py results` exit code, not an
assumed one. iter-27b: the strongest available "no writes happened" proof is a `mode=ro` connection
that refuses a control `CREATE TABLE`, not a row count — reused again this round for both backend boots.

**Safety note (not a `Maintenance isolation:` line — the backend must stay up and browser-QA must run
for the ten required journeys; this is a request for host quietness during the measurement window
only).** The extended re-measurement touches the part of the program that uses the most memory, on the
same host a run of this system froze on 2026-08-20. Nothing else of this project's (or a sibling
project's) goal-mode work should run concurrently during either sampling window; this is a non-blocking
owner-facing note, not a hard engine control this agent is authorized to declare.

**Two open owner points carried forward, neither blocking:** (a) the owner may accept 2,467,888 kB
(iter-33's figure) or this round's fresh figure as-is and treat this iteration as a confirmation only —
nothing here requires that ruling to complete; (b) if the owner would rather no further code ever touch
the warm-up path, this iteration already honors that (OUT OF SCOPE below forbids touching it).

## IN SCOPE

### Backend (Trendora measurement only — zero application code change; binding "Do not redo": J-09's
`warmup.py`/`prices.py` mechanism is CLOSED and must not be touched)
- [ ] Re-run J-09's standing-warm memory measurement over an EXTENDED window: sample
  `/proc/<pid>/status` at 1-second intervals for **≥360 seconds** post-backend-start (`bash
  scripts/start-backend.sh`), recording `VmPeak_kB`, `VmSize_kB`, AND `VmRSS_kB` every row for the
  single sampled pid — not `VmPeak` alone.
- [ ] Independently repeat the identical measurement a second time, from a FRESH backend boot, as the
  auditor's own from-scratch re-derivation (not a copy of the developer's numbers) — this iteration's
  genuine full depth restores the auditor step iter-33 silently dropped, and directly answers the prior
  evaluator's "have the independent checker take the measurement again from scratch" request.
- [ ] Append ONE new dated Addendum 45 to `reports/perf-budgets.md` (append-only — verify via `git diff
  --stat reports/perf-budgets.md` showing only `+N/-0`) recording, for BOTH runs: max `VmPeak_kB` across
  the full window vs the 2,621,440 kB bar and vs iter-33's 2,467,888 kB; and the settled `VmRSS_kB` /
  `VmSize_kB` pair read at the row where `VmPeak_kB` last increased (the plateau), reported as a figure
  distinct from the high-water mark.
- [ ] Re-run the byte-identity spot check (`cmp`) over the same authorized `as_of` value set used at
  iter-33 (7 values × `/api/compass` + `/api/dashboard` = 16 captures) against the current backend;
  record compared/differing counts in the dev handoff.
- [ ] Re-prove zero database writes across BOTH backend boots this round using the iter-27b method (a
  control connection opened `mode=ro` that must refuse a `CREATE TABLE`) plus the `.db` file's mtime and
  WAL byte-size compared before vs after both boots.

### Backend (Goal Mode harness/automation only — no Trendora application code; patch
`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` and, only if required,
`goal_gate.py`; `scripts/` is a tracked symlink into `incredible_auto_dev/scripts/` — patch the one real
file, never both copies)
- [ ] Give a target/required journey whose `docs/goal.md` Acceptance text carries the literal marker
  `**Walkthrough:** waived` (already present verbatim for J-09, J-10, J-11) a way to be recorded as
  verified in the merged `ui-test-results.md` through cited non-UI evidence — e.g. a `UT-J-09` row whose
  Evidence cell names the new Addendum 45 entry and the sampler CSV paths — instead of being forced to
  `BLOCKED` by `missing_target_journeys`/`missing_required_journeys` purely for having no browser row.
  Scope the exemption STRICTLY to journeys carrying that literal `docs/goal.md` marker (read from
  `docs/goal.md` itself, never journey-ID pattern-matching alone), so no other journey's missing
  verification can be silently waived.
- [ ] Add a focused regression test proving BOTH directions: (a) a walkthrough-waived target journey
  with a cited-evidence row no longer forces `BLOCKED`; (b) a target/required journey WITHOUT that
  goal.md marker, missing or SKIP-only, still forces `BLOCKED` exactly as before the fix (iter-41/42's
  own guard must not regress into a general loophole).
- [ ] Re-run `python3 scripts/automation/lib/goal_gate.py results
  reports/phase-goal-market-compass-iter-34-ui-test-results.md` after the merge and record its OBSERVED
  exit code and headline verdict directly in the dev handoff — never asserted from memory (iter-32's
  "a gate that asserts an artifact without opening it" lesson).

### Frontend
- None. J-09's own Acceptance waives its walkthrough; the harness fix touches no UI surface; all ten
  Required-still-passing journeys are re-verified through pages that already exist — no new page or
  component this iteration.

### New user-facing capability
None this iteration — this is a closing confirmation + tooling round, not a product-surface build
(binding "Do not redo": J-09's mechanism is CLOSED).

### New information displayed
None — no new page, card, or field.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The product experience served to a user is unchanged; only the internal memory-measurement
evidence and the goal-mode harness's own evidence bookkeeping change.

### Blueprint conformance
No new surfaces. This iteration's only artifacts are a `reports/perf-budgets.md` addendum and a
goal-mode harness fix, matching the informational-note precedent already recorded for iter-25/32/33 in
`runs/goal-session-market-compass/state/blueprint.md` (memory measurements and harness fixes sit outside
the Information Architecture and Data Contract). An iter-34 note is appended to `blueprint.md` recording
this explicitly.

### Data-contract additions
None. No new displayed value, computing module, or serving endpoint is introduced.

## OUT OF SCOPE

- Any change to `apps/backend/app/engine/warmup.py`'s cadence loop or
  `apps/backend/app/engine/prices.py`'s `_BarCache`/`bar_cache`/`prefill` — binding "Do not redo": J-09's
  mechanism is CLOSED; this iteration CONFIRMS, it does not rebuild.
- Widening the 2.5 GB target, or touching `memory_cap_mb`, `pool_size`, `max_overflow`, or
  `project-extensions/host-guard/host-guard.env` — owner-only (AG-10).
- The carried, non-blocking items from iter-33's log: J-04's candidate-card screenshot re-take (16th
  round owed); J-02/J-03/J-05/J-06/J-08's recorded walkthroughs; J-07's four-step recording; the two
  pre-existing red unit tests on files this iteration does not touch; the "What changed"/"Leadership
  rotation" identical-rows cosmetic note; the iteration-23 throwaway clone; `apps/frontend/.next-verify/`
  tracked in git; J-01's automatic re-check assertion strength; the `browser_checks_run: false`
  bookkeeping flag despite screenshots existing. None are blocking, none touch this iteration's
  harness/measurement scope, and bundling them risks an undiagnosable mixed result (priority rubric
  rule 5).
- The five older owner questions carried since iter-31/32/33 (J-06 wording, J-01's first two test
  steps, empty "next-session focus" acceptability, MNST recovery-list membership, the 12 August
  "rebuilt" note) — non-blocking, remain open for the owner.
- Re-litigating whether Constraints (c)'s shipped boolean switch is the literal "configured memory
  budget" the goal text names — recorded as a wording gap at iter-33, not reopened this round.

## DEFINITION OF DONE

- [ ] Target journey J-09 reconfirmed: extended (≥360s) `VmPeak`/`VmSize`/`VmRSS` measurement taken
  TWICE (developer run + independent auditor re-derivation), Addendum 45 appended append-only, byte-
  identity spot check clean, zero-write proof clean (TC-1..TC-6)
- [ ] The merged `ui-test-results.md`'s J-09 evidence row is non-`BLOCKED` and
  `goal_gate.py results` exits 0 on this iteration's merged file, with the exemption proven not to
  generalize to unwaived journeys (TC-7, TC-8)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10, J-11 remain
  green via deterministic replay + LLM fallback, with golden-script hygiene confirmed clean for a third
  round (TC-9)
- [ ] No anti-goal violation introduced (AG-3 correctness held by the byte-identity spot check, AG-10
  host ceiling respected — no cap value touched, AG-12 manifest immutability held by J-05/J-06's clean
  replay)
- [ ] Unit tests covering this iteration's changed files pass; no new regressions (TC-8, TC-11); the two
  pre-existing unrelated red tests remain carried, explicitly named in the dev handoff, not silently
  fixed and not silently ignored
- [ ] The dispatched depth is stated explicitly, in words, in the dev handoff, cross-checked against
  `runs/goal-market-compass-iter-34/.steps/` markers; any demotion is disclosed per
  `docs/goal.md:2423-2436`, never silent (TC-10)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-34-dev.md`

## TESTING REQUIREMENTS

- Browser: J-09 has no UI surface (walkthrough waived by `docs/goal.md`); browser-qa-agent instead
  re-verifies the ten Required-still-passing journeys (J-01..J-08, J-10, J-11), live and/or via
  deterministic replay.
- Unit/integration: `merge_ui_test_results.py`'s self-test suite (existing cases plus the two new TC-8
  cases); a direct invocation of `goal_gate.py results` against this iteration's merged file; the
  sampler/measurement tooling exercised by its own existing fixture tests.
- Error cases: a target/required journey that does NOT carry the goal.md waiver marker must still force
  `BLOCKED` when missing or SKIP-only (TC-8b); an Addendum-45 append that is not strictly `+N/-0` must
  be treated as a defect, not silently accepted (TC-3).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line below.

- TC-1: given a quiet host (no other goal-mode engine or heavy job running concurrently) with J-09's
  config unchanged (`cache_size -65536`, `pool_size 24`, `max_overflow 44`,
  `startup.warmup_bar_cache_bounded` untouched), when the developer samples `/proc/<pid>/status` at
  1-second intervals for ≥360 seconds after a backend start via `bash scripts/start-backend.sh`, then a
  new CSV file contains ≥360 rows with `VmPeak_kB`, `VmSize_kB`, and `VmRSS_kB` columns for the single
  sampled pid.
- TC-2: given that same host state, when the auditor independently repeats the identical measurement
  from a FRESH backend boot (not copying the developer's numbers), then a second, independently
  generated CSV exists with its own ≥360 rows and its own computed max `VmPeak_kB` figure.
- TC-3: given both CSVs, when max(`VmPeak_kB`) is computed over each file's full row set, then Addendum
  45 in `reports/perf-budgets.md` states both figures explicitly compared to the 2,621,440 kB bar and to
  iter-33's 2,467,888 kB figure, and `git diff --stat reports/perf-budgets.md` shows only `+N/-0`.
- TC-4: given the same two CSVs, when the settled `VmRSS_kB`/`VmSize_kB` pair is read at the row where
  `VmPeak_kB` last increased (the plateau, not the final sampled row), then that steady-state pair is
  recorded in Addendum 45 as a figure distinct from the `VmPeak` high-water mark, for both runs.
- TC-5: given the extended re-run's live backend, when `cmp` is run over the same 16 before/after
  `/api/compass` + `/api/dashboard` captures (7 authorized `as_of` values) used at iter-33, then the dev
  handoff records exactly "16 compared, 0 differing" (or the honest non-zero count if any differ).
- TC-6: given both backend boots this round, when a control connection opened `mode=ro` attempts a
  `CREATE TABLE` against `apps/backend/data/trendora.db`, then it is refused, AND the `.db` file's mtime
  plus WAL byte-size are unchanged when compared before vs after both boots.
- TC-7: given `docs/goal.md`'s J-09 Acceptance carries the literal marker `**Walkthrough:** waived`,
  when the merge/gate fix ships and this iteration's replay + browser-qa lanes finish, then the merged
  `reports/phase-goal-market-compass-iter-34-ui-test-results.md` carries a J-09 evidence row whose
  Evidence cell cites Addendum 45 and the sampler CSV paths, with a non-`BLOCKED` verdict, AND `python3
  scripts/automation/lib/goal_gate.py results reports/phase-goal-market-compass-iter-34-ui-test-results.md`
  exits 0 (observed and recorded, not assumed).
- TC-8: given the new regression test added alongside `merge_ui_test_results.py`'s existing self-tests,
  when it is run against (a) a synthetic waived-marker target journey with a cited-evidence row, then the
  merged headline is non-`BLOCKED`; and (b) a synthetic target journey WITHOUT the goal.md marker that is
  missing/SKIP-only, then the merged headline is still forced to `BLOCKED` exactly as before the fix.
- TC-9: given the ten Required-still-passing journeys, when the deterministic replay lane executes their
  golden scripts, then all ten produce PASS rows in the merged results file AND every
  `journey-scripts/*.json` mtime predates this iteration's replay-run timestamp (golden-script hygiene,
  third clean round running).
- TC-10: given this spec's `Depth: full` (mandatory per prior ESCALATE), when the iteration completes,
  then the dev handoff contains an explicit sentence stating the depth that actually dispatched,
  cross-checked against `runs/goal-market-compass-iter-34/.steps/` containing `auditor.done`, a
  QA-or-browser-qa completion marker, `closure.done`, and `ux-regression.done`; if any marker is absent,
  the handoff discloses the demotion explicitly per `docs/goal.md:2423-2436` rather than omitting it.
- TC-11: given the two pre-existing red unit tests unrelated to this iteration's changed files, when the
  developer's own test run for changed files (`merge_ui_test_results.py`, `goal_gate.py`, any sampler
  script) completes, then it reports 0 new failures among those files, and the dev handoff names the two
  pre-existing failures explicitly as carried, neither fixed nor silently ignored.

## NOTES

- This iteration is deliberately a CLOSING CHECK, not new building — all eleven journeys already pass
  and the binding "Do not redo" list forbids touching J-09's shipped mechanism. Its two deliverables
  (an independently-corroborated, longer-window measurement; and a merge/gate fix so J-09's substitute
  evidence actually registers) are exactly what iter-33's ESCALATE named as the remaining path to a
  legitimate `GOAL_ACHIEVED` recommendation.
- If, after this iteration, the deterministic gate returns clean and the independent re-measurement
  corroborates iter-33's figure (or lands under the bar on its own), the next evaluator has everything
  needed to consider `GOAL_ACHIEVED` without another engineering round — but that call belongs to the
  evaluator, not this spec.
- Assumption-ledger entry logged this iteration (see
  `runs/goal-session-market-compass/state/assumptions.md`, `## iter-34 — goal-decomposer`): the reading
  chosen for "fix the results file" (a scoped harness code change keyed to goal.md's literal waiver
  marker, not a one-off manual edit of a single report) and for treating J-09 as a legitimate `Target
  journeys` entry despite the binding "Do not redo" (the do-not-redo blocks rebuilding the MECHANISM,
  not re-verifying it).
