# Goal Iteration 53 — Extend the finalize-tail scheduling fix to coverage/membership-timeline and market-phase warm

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 53
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the last evaluator verdict (iter-52) was ESCALATE, which mandates full depth with no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-04, J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-08, J-09
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Extend iter-52's proven cooperative-scheduling fix (`_cooperative_sorted` / `_cyclic_gc_paused`) from
`compute_factor_lab_all` to the two ingest finalize-tail phases it deliberately left untreated —
`coverage_membership_timeline_refresh` and `market_phase_warm` — so a heavy data job's remaining
connection-level `GET /api/health` non-answers (2 of 1,285 in the last concurrent drill) close to zero,
and capture J-04's last unobserved evidence (badge/banner + logfile) in the same lane pass.

## BACKGROUND

Iter-52 ESCALATEd: it diagnosed and fixed the real cause of `/api/health` going unanswered during a data
job (GIL contention from an uninterrupted CPU-bound loop — iter-50's own lesson, "bounding memory cannot
close a responsiveness requirement"), but the fix landed *after* the 8-journey lane had already run
(TC-9, breached 6 of 7 rounds), so the lane's own evidence was stale and the round's scoreboard did not
move. The iter-52 evaluator's next-step recommendation, read together with `reports/perf-budgets.md`
Addendum 14's own "what is still open" section, is unambiguous about the next concrete action: of the
two live connection-level non-answers Addendum 14's concurrent drill measured, both landed inside
`coverage_membership_timeline_refresh` and `market_phase_warm` — the two finalize-tail phases iter-52's
fix pass was explicitly licensed to leave untouched (it was scoped to the audit's findings only). This
iteration finishes that named work. Per the priority rubric: this is an **unblocker** (J-05 step 4 and
J-07 step 2 share the exact same root cause and the exact same fix mechanism, so treating both phases in
one pass closes evidence gaps on two journeys at once) and is the **smallest concrete next step** — the
diagnosis pattern is proven, only the profiling-and-application work remains, so this is not a second
undiagnosed risky change (rule 6). J-04 rides along for free: its boot + interrupted-job behavior is
already proven code (iteration-state.md "Do not redo"); only its badge/banner and logfile evidence were
never captured, and the 8-journey lane this iteration must run anyway (per TC-9) will capture it at no
marginal cost (rule 7's piggyback allowance — this is not an evidence-only iteration; it carries real
dev scope).

**Deliberate scope narrowing, stated per self-check 5.** J-06 (Regime Lab MemoryError + its golden's
heading-only assertion) is a **separate, undiagnosed** defect (iter-52/cn, deferred 18 rounds) in a
different module (`_regime_lab_members_by_horizon`) with no profiling done yet. Bundling its diagnosis
into this iteration would stack a second risky, undiagnosed change onto the one this spec already
carries (rule 6 explicitly forbids this) — deferred to a future iteration in full. Strengthening only
the golden's assertion without also fixing the underlying MemoryError would produce a DoD checkbox this
iteration cannot honestly satisfy (the corrected assertion would then legitimately FAIL), which is
exactly the "Definition-of-Done honesty" violation class already flagged twice this session
(iter-52/ck) — so the golden fix ships together with the real fix, not ahead of it. `forward_aggregates_warm`
is also named as untreated in Addendum 14 and carries the largest slow-poll count (15/34 >2.0s), but
produced **zero** connection-level non-answers — the higher-severity defect class this iteration targets
— so it is deliberately deferred; logged to `assumptions.md` (iter-53) with the cost stated honestly:
the 1,200s finalize-tail concurrent-load budget will likely still read over budget after this iteration.

**Lessons applied (from `lessons.md`, matched by "Applies to"):** (1) iter-50's second lesson —
bounding memory cannot fix a scheduling problem; this iteration is scheduling-only, `memory_cap_mb`/
`malloc_arena_max` stay untouched. (2) iter-49's second lesson — a wall-clock/memory bound proven only
solo is not proven in the product; TESTING REQUIREMENTS below mandate the SAME concurrent-drill
methodology Addendum 14 already established (dedicated `/api/health` poller + dedicated heavy-request
stream + the ingest job, all at once), not a solo-only measurement. (3) iter-48's first lesson — read
every phase's own timing row before naming a bottleneck; the developer must profile
`coverage_membership_timeline_refresh` and `market_phase_warm` themselves rather than assuming the
GIL-hold site is a `sorted()` call by analogy to `compute_factor_lab_all`. (4) iter-51/iter-52's TC-9
lessons — the lane-before-audit-fix pipeline ordering has broken 6 of 7 rounds; this iteration
operationalizes the standing fix (audit files a note, not a code change, if it finds something after
the lane has run) as an explicit, binding rule below rather than leaving it to the auditor's judgement
again.

## IN SCOPE

### Backend
- [ ] Profile `coverage_membership_timeline_refresh` (`refresh_coverage_snapshot` →
      `_compute_coverage_uncached` → `membership_timeline_cached`, `app.engine.data_manager`) under a
      concurrent drill (Addendum 14's methodology) to find which call actually holds the GIL longest,
      then apply the proven pattern — `_cooperative_sorted` (chunked stable sort) and/or
      `_cyclic_gc_paused` (bounded GC pause), or an equivalent chunked/bounded construct if profiling
      shows a different operation dominates — to that call, mirroring `compute_factor_lab_all`'s
      profile-first (not guess-first) methodology.
- [ ] Profile `market_phase_warm` (`market_phase.market_phase_cached` → `compute_market_phase`,
      `app.engine.market_phase`) the same way and apply the same treatment to whichever call inside it
      is the actual GIL-hold source.
- [ ] Preserve the existing per-phase `MemoryError` isolate-and-continue contract (iter-8: on
      `MemoryError`, stop the current loop, call `_release_process_memory()`, keep already-completed
      items honestly reported) unchanged for both phases.
- [ ] Add unit tests asserting the treated function's output is identical (object-identity or
      value-equality, matching `test_research_streaming.py`'s existing convention) to the untreated
      computation for the same fixture inputs, in `test_data_manager_membership_cache.py` /
      `test_data_manager.py` (coverage/membership-timeline) and `test_market_phase.py` (market phase).
- [ ] Re-run the solo + concurrent drills against the shipped tree (Addendum 14's exact methodology:
      dedicated 1/s `/api/health` poller process, dedicated heavy-research-request stream, one
      backfill job) and append a new dated addendum to `reports/perf-budgets.md` disclosing the
      measured non-answer count, the >2.0s poll count, and the finalize-tail total honestly — met or
      not met, never rounded up.

### Frontend

None — Frontend Present: no. J-04's evidence capture below observes existing, already-shipped UI; no
frontend file changes are anticipated.

### New user-facing capability

None. This is a reliability/scheduling fix inside already-shipped ingest finalize-tail phases — nothing
new is exposed to the user. J-04's already-built badge/banner/logfile behavior gets its first evidence
capture (no new behavior, only new proof of existing behavior).

### New information displayed

None.

### New user actions

None.

### UI surface changes

None. Browser-qa observes EXISTING surfaces only — the top-bar readiness badge, the preflight banner,
and the `/data` job-history panel — to capture J-04's previously-unobserved steps.

### Product surface delta

`GET /api/health` answers more reliably (fewer/zero connection-level non-answers) while a
backfill/rebuild job's `coverage_membership_timeline_refresh` and `market_phase_warm` finalize-tail
phases run. Invisible as a new feature; measurable as fewer stalls during a data job.

### Blueprint conformance

No new page, route, or nav entry. This iteration's work lives entirely under the ALREADY-registered
Data Contract rows "Coverage payload," "Regime score, market phase, realized forward-returns," and
"Membership timeline / research hot-key caches" (`runs/goal-session-ops-hardening/state/blueprint.md`),
all served from their existing `/data` (Data Manager) home; J-04's evidence capture is on the existing
global readiness badge + preflight banner + `/data` job-history home. `blueprint.md` has already been
updated (additive-only: a new "iter-53 update" changelog paragraph, plus the iter-52 coherence-auditor's
requested Notes correction on the "Membership timeline / research hot-key caches" row) — no nav-skeleton
change, no reapproval file needed.

### Data-contract additions

None. No new displayed value, field, table, or endpoint. This iteration bounds GIL-hold time inside
functions that are ALREADY each Data Contract row's single canonical computing module
(`app.engine.data_manager` for Coverage payload / Membership timeline; `app.engine.market_phase` for the
market-phase row), served by their EXISTING single endpoints — no second producer is introduced for any
registered value.

## OUT OF SCOPE

- The Regime Lab `/research/regime-lab` MemoryError (`compute_regime_lab` →
  `_regime_lab_members_by_horizon`, AG-8, iter-52/cn) and `J-06.json` step 11's heading-only assertion —
  a separate, undiagnosed defect (18-round-deferred, iter-33/g); bundling its diagnosis here would stack
  a second risky, undiagnosed change onto this iteration (rule 6). Deferred to a future iteration, golden
  fix and root-cause fix together (see BACKGROUND).
- `forward_aggregates_warm`'s untreated GIL-hold (Addendum 14's third named phase, 15/34 slow-but-answered
  polls, zero non-answers) — deferred; logged to `assumptions.md` (iter-53).
- Closing the finalize tail's concurrent-load TC-5 budget (1,200s; currently 1,261.42s, 5.1% over) —
  likely still not fully closed after this iteration, since `forward_aggregates_warm` (738.70s) and
  `drawdown_expectations_warm` (411.89s), the two largest concurrent-load contributors, are untouched.
  Not claimed as closed.
- Moving heavy compute to a separate process/worker boundary — unresolved owner decision (asked iters
  50, 51; still unanswered). Continuing the in-process scheduling treatment, consistent with iters 51/52.
- The health check's ~0.14s per-poll real DB work, and the overlapping-request race that can quietly
  cancel the memory-pause protection — both small, previously disclosed findings, not this iteration's
  scope.
- Long-carried backlog items (iter-29/b through iter-48/bj, ledger-tracked) — untouched, not
  re-litigated here.
- Walkthrough/demo capture repair (this session's JSON parse error on the demo recorder; J-07's own
  walkthrough, 22 rounds unrecorded) — capture-only per rule 7, not mandated as this iteration's
  deliverable.
- The stale dev-handoff/design-record completeness gap on iter-52's OWN handoff — historical record, not
  retroactively edited; iter-53 gets its own fresh, complete handoff.

## DEFINITION OF DONE

- [ ] `coverage_membership_timeline_refresh` and `market_phase_warm` both apply a profiled,
      chunked/bounded cooperative-scheduling treatment; a new unit test proves byte-identical output for
      each (TC-3).
- [ ] A concurrent drill using Addendum 14's exact methodology measures the `/api/health` non-answer
      count attributable to those two phases specifically, and the result — zero, or the honest measured
      count if not zero — is recorded in a new `reports/perf-budgets.md` addendum (TC-1, TC-2).
- [ ] The existing per-phase `MemoryError` isolate-and-continue contract is unchanged for both phases,
      verified by a fault-injection test (TC-5).
- [ ] J-04 steps 3-5 (badge/banner initializing detail, crashed/unreachable presentation, persistent
      logfile truncation) get their first evidence capture via browser-qa-agent (TC-6).
- [ ] The 8-journey deterministic-replay + browser-qa lane (all 8, including this iteration's three
      targets) is dispatched LAST against a tree frozen after this iteration's code lands; if the audit
      step subsequently finds a defect needing a product-code change, it is filed as a note for iter-54
      rather than applied as a code-changing audit-fix, so this iteration's own lane evidence stays valid
      for the tree it measured (TC-7).
- [ ] Required-still-passing journeys J-01, J-03, J-08, J-09 replay PASS (TC-7).
- [ ] No anti-goal violation introduced: AG-8's MemoryError isolate-continue contract holds (TC-5); AG-9
      all ingest rows created this iteration read `provider='seed'` (TC-8); AG-10's five frozen
      launch-script/config surfaces show an empty `git diff`/`git status --porcelain` (TC-8).
- [ ] Unit tests pass; no regressions in the existing backend test suite (TC-3, TC-4, TC-5).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-53-dev.md`, naming both treated
      phases, their profiled GIL-hold source, and the concurrent-drill result honestly, met or not met
      (TC-9).

## TESTING REQUIREMENTS

- Browser: J-04 (steps 3, 4, 5 — badge/banner + logfile evidence capture), J-05 (step 4 — health
  responsiveness during ingest), J-07 (step 2 — health responsiveness during forward-aggregate warm) as
  primary targets; J-01, J-03, J-08, J-09 as required-still-passing deterministic replay.
- Unit/integration: `test_data_manager_membership_cache.py` / `test_data_manager.py` (coverage +
  membership-timeline byte-identity and MemoryError-isolation for the new treatment),
  `test_market_phase.py` (market-phase byte-identity and MemoryError-isolation), plus a live
  spawned-backend concurrent drill mirroring `reports/perf-budgets.md` Addendum 14's methodology.
- Error cases: a `MemoryError` injected into either newly-treated phase's loop must stop only that
  loop, call `_release_process_memory()`, and leave every already-completed item/date in
  `aggregates_refreshed` honestly reported — never crash the finalize tail or the process, never silently
  drop an already-succeeded item.

Test-first contract:

- TC-1: given the backend running under AG-10 caps with a concurrent heavy-request stream (Addendum
  14's methodology — a dedicated `/api/health` poller at 1/s, a dedicated backfill job, a dedicated
  heavy-research-request stream), when the `coverage_membership_timeline_refresh` and `market_phase_warm`
  finalize-tail phases run, then zero `/api/health` polls tagged to those two phases return a
  connection-level non-answer (no HTTP status within the 5.0s client ceiling) — down from the 2 recorded
  in Addendum 14.
- TC-2: given the same concurrent drill, when it completes, then `reports/perf-budgets.md` gains a new
  dated addendum recording each phase's concurrent elapsed seconds and the count/percentage of
  `/api/health` polls exceeding 2.0s attributable to `coverage_membership_timeline_refresh` and
  `market_phase_warm` specifically, disclosed honestly whether or not the ≤2s ceiling is fully met for
  those two phases.
- TC-3: given the new chunked/bounded treatment applied inside
  `_compute_coverage_uncached`/`membership_timeline_cached` and/or `compute_market_phase`, when a new
  unit test runs the treated function against the same fixture inputs as the untreated computation, then
  the two outputs are asserted equal (object-identity or value-equality, matching
  `test_cooperative_sorted_is_byte_identical_to_sorted_across_the_chunk_boundary`'s convention) for every
  affected date/symbol.
- TC-4: given a solo (non-concurrent) ingest job with both new treatments applied, when
  `_refresh_ingest_aggregates` runs to completion, then `aggregates_refreshed` still lists `coverage`,
  `membership_timeline`, and `market_phase` exactly as before, with zero new `MemoryError` recorded in
  `logs/backend.log` for that run's segment.
- TC-5: given `_fault_inject_memory_error` armed on either newly-treated phase (mirroring the existing
  `factor_lab_all` fault-injection convention), when that phase's loop hits the injected `MemoryError`,
  then the loop stops immediately, `_release_process_memory()` is called, and every date/item that
  already succeeded earlier in that same loop is still listed in `aggregates_refreshed` — the process
  does not crash and `GET /api/health` keeps answering 200 throughout.
- TC-6: given J-04's boot + interrupted-job behavior is already-proven, unchanged code, when the
  browser-qa lane executes J-04 steps 3-5, then (a) a screenshot/DOM assertion captures the top-bar
  badge showing the initializing-phase detail (phase + `n/m` progress) during a pre-ready poll window,
  (b) a screenshot/DOM assertion captures the distinct crashed/unreachable presentation after the
  simulated kill, and (c) the persistent backend logfile is opened and asserted to contain boot entries
  with no clean-shutdown entry following the kill.
- TC-7: given both new treatments have landed and the working tree is frozen, when the 8-journey
  deterministic-replay + browser-qa lane is dispatched (covering J-01, J-03, J-04, J-05, J-07, J-08,
  J-09 and J-06 as already-standing), then every lane result file's mtime is strictly after the newest
  `apps/backend/**` product-code mtime, J-01/J-03/J-08/J-09 replay PASS, and if the audit step
  subsequently identifies a defect needing a code change, the audit report names it as a finding for
  iter-54 rather than the developer applying a code-changing audit-fix after the lane has run.
- TC-8: given the five frozen AG-10 surfaces (`config.yaml`, `host-guard.env`,
  `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh`), when this iteration's diff
  is checked, then `git diff --stat` and `git status --porcelain` over those five paths are both empty,
  and every `data_provider_runs` row created during this iteration's drills reads `provider='seed'`.
- TC-9: given this iteration's dev work is complete, when the developer finishes, then
  `docs/handoffs/goal-ops-hardening-iter-53-dev.md` exists and names both treated phases, the specific
  call each profile identified as the GIL-hold source, and the concurrent-drill result stated honestly
  (met or not met against the ≤2s ceiling and the 1,200s finalize-tail budget).

## NOTES

- **Owner asks, carried forward again (unanswered since iter-50/51):** (a) may a future round move heavy
  compute into a separate process/worker boundary — still the only way to guarantee `/api/health` never
  pauses at all? (b) is the 1,200s finalize-tail budget meant to hold only when the app is idle, or also
  while it is serving concurrent traffic — it was met idle (955.75s) and missed by 5.1% busy (1,261.42s)?
  Neither blocks this iteration's chosen scope (extending an already-proven in-process pattern to two
  more phases is agent work either way), but both remain open decisions only the owner can make.
- **Assumption logged:** `runs/goal-session-ops-hardening/state/assumptions.md` (iter-53) records the
  2-phases-vs-3-phases scoping call (why `forward_aggregates_warm` is deferred despite perf-budgets.md
  naming it alongside the two treated phases) and its cost.
- **Blueprint already updated** (additive-only, done by this decomposer): a new "iter-53 update"
  changelog paragraph, and the iter-52 coherence-auditor's requested Notes correction on the
  "Membership timeline / research hot-key caches" row (documenting the mechanism iter-52 actually shipped
  — `_cooperative_sorted`/`_cyclic_gc_paused` after a first plain-yield pass measured worse — rather than
  the earlier, incomplete "periodic cooperative-yield points" description).
- If the developer's profiling of either phase finds the GIL-hold source is NOT a `sorted()`/GC-pause
  shape at all (e.g., a different bulk allocation), apply whichever chunked/bounded construct the
  profile actually supports — do not force-fit `_cooperative_sorted`/`_cyclic_gc_paused` onto a
  mismatched bottleneck; name the real one in the dev handoff instead (iter-48's lesson: profile, don't
  guess).
