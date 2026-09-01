# Goal Iteration 32 — J-09 clean memory re-measurement with durable raw evidence

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 32
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was `ESCALATE` (iter-31); rule 3 ("Prior ESCALATE") makes full
  depth mandatory this iteration, no exceptions. This also matches the evaluator's own binding
  depth recommendation for iter-32.
- **Frontend Present:** no
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10, J-11
  (full regression widening — see BACKGROUND)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
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

## GOAL

Produce an honest, durably-evidenced re-measurement of J-09's standing-warm backend memory
footprint — the last open journey in this session — replacing the two prior figures (iter-4's
3,439,100 kB and iter-25's 3,064,772 kB, the latter now known to rest on no surviving raw capture,
a second competing goal-mode engine on the host, and ~2x the documented load) with a clean number
captured on a quiet host with its raw sampler output saved to a durable file.

## BACKGROUND

iter-31 (ESCALATE) found that six evaluators in a row had carried J-09's "~2.99 GB acceptability"
as an owner-gated open question, but the iter-25 measurement backing that figure has no surviving
`/proc` capture or sampler log, ran while a second goal-mode engine (`tensteps`) held the host, and
was sampled under roughly 2x the documented request volume — so the blocker is an evidence gap,
not an owner decision (lesson: "any iteration about to record, carry, or act on a 'waiting on the
owner' blocker — open the underlying measurement and check whether primary evidence actually
survives"). J-09's own config change (`cache_size` `-262144` → `-65536`) already landed at iter-4
and is unchanged since (verified read-only against `config.yaml:109` and `pool_size`/`max_overflow`
at `126-127`, still 24/44) — this iteration is a pure re-measurement, not a code change, unless
verification finds drift.

Depth is `full` because the prior verdict was `ESCALATE` (rule 3, mandatory). The evaluator's own
depth recommendation for iter-32 is `full`, matching. This is also the ninth time this session a
`full`-required iteration risks demotion to `lean` (iters 2, 6, 8, 23, 24, 26, 28, 31 all demoted) —
`docs/goal.md`'s loop-mechanics section states demotion "MUST be surfaced explicitly and MUST NOT
silently fall back to `lean`"; if the engine demotes this spec again, the dev handoff must say so in
terms, not paper over it.

**Two repair items ride along, per iter-31's explicit recommendation, both mechanical, neither a new
build:** (1) `journey-scripts/J-02.json` and `journey-scripts/J-03.json` were rewritten by the
browser-qa lane at iter-31 (mtimes 03:35:14 / 03:35:18, AFTER that round's replay results were
already written at 03:31:03) and have never been executed — including both in Required-still-passing
above means this iteration's deterministic replay lane runs them for the first time; report the real
result verbatim and do not edit either script again afterward regardless of outcome (this is the
fourth recurrence of the "golden rewritten after replay is not coverage" defect — iters 29/30/31 —
so Required-still-passing is widened to the full ten-journey passing set this round, both to close
this gap and because a prior-ESCALATE round is exactly when `docs/goal.md`'s own loop-mechanics
guidance calls for widening regression to refresh goldens and catch drift). (2) the rewritten
`J-02.json` golden asserts the literal string "Suppressed moves (36)", a count tied to one stored
date — flagged here for awareness; this iteration performs no manifest-affecting write, so the
count cannot move.

**Safety note for the human operator (plain prose, not a config line — this is not a destructive
migration or a damaged-data repair, so neither `Depth enforcement: required` nor
`Maintenance isolation: required` applies; the measurement needs the backend booted, which
`Maintenance isolation` would block):** J-09's steps 2 and 4 deliberately load-burst the same
26.7 GB host that a goal-mode run froze via swap-thrash on 2026-08-20. Nothing else of ours —
in particular no sibling goal-mode/tensteps session — should be running on this host while this
iteration's measurement executes; iter-25's own contaminated reading is the proof of what happens
otherwise. If a quiet host cannot be guaranteed, the dev handoff must say so plainly rather than
present a burst-under-contention figure as clean.

`test_no_magic_numbers.py`'s pre-existing red failure on three untouched files
(`indicators.py`/`forward_testing.py`/`research.py`) is out of scope (owner's call, carried since
iter-31 and earlier).

## IN SCOPE

### Backend
- [ ] Confirm `config.yaml`'s `database.pragmas.cache_size` still reads `-65536` (set at iter-4) and
      `pool_size`/`max_overflow` still read `24`/`44` — no edit expected; if drift is found, restore
      `-65536` and note it, changing nothing else in the `database:` block.
- [ ] Start a fresh backend via `bash scripts/start-backend.sh` on a host with nothing else of ours
      running; wait for standing-warm plateau (readiness `ready`, VmPeak flat across ≥3 consecutive
      samples); read `/proc/<pid>/status` `VmPeak` and save the raw capture (UTC start/end
      timestamps, every sample, not just the peak) to a durable file under
      `runs/goal-market-compass-iter-32/` (e.g. `j09-vmpeak-samples.csv` or `.log`) that survives
      after the iteration — this is the evidence iter-25's figure lacked.
- [ ] Re-run the iter-71-class concurrent-load check (a request burst at `server.limit_concurrency`
      = 64 simultaneous connections) against the same running backend; record pass/fail (zero
      `QueuePool` `TimeoutError`, zero non-200s attributable to pool starvation).
- [ ] Byte-identity spot-check: capture `GET /api/compass` (plus 1-2 other already-served read
      endpoints) for a fixed already-manifested `as_of` from the safe set
      `{no param (frontier, 2026-08-12), "2025-04-15", "1996-02-01"}` — the same set bound at
      iter-31 to guarantee zero new manifest mints — before and after this iteration's change (or
      confirmed non-change) to `cache_size`; cite the byte-identical result in the dev handoff.
- [ ] Append ONE new dated addendum to `reports/perf-budgets.md` (next sequential Addendum number
      after the current highest — do not renumber or edit Addendum 40/41/42) recording: the measured
      VmPeak in kB and MB, the comparison to the ≤ 2,621,440 kB (2.5 GB) target, the comparison to
      iter-4's (3,439,100 kB) and iter-25's (3,064,772 kB, now flagged unsupported) figures, the
      concurrent-load check result, the byte-identity spot-check result, and a citation of the raw
      evidence file path from the step above with its capture start/end UTC timestamps.
- [ ] If the ≤ 2.5 GB target is still missed on this clean measurement: record the honest figure,
      do NOT widen the target, and state plainly in the dev handoff that owner review is the
      remaining path — never fabricate or round a passing number.

### Frontend
- None — J-09's own Walkthrough clause is waived (deliberately backend-only, no UI surface change;
  no displayed value may move, proven by the byte-identity spot-check above).

### New user-facing capability
None — J-09 is an internal resource-footprint fix with no new UI surface.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to a user; `reports/perf-budgets.md` gains one dated addendum (an internal ops report,
outside the product's Information Architecture).

### Blueprint conformance
No new surfaces — J-09 touches no page in the Information Architecture; `blueprint.md` gets an
informational iter-32 note only (no IA or Data Contract row changes), matching the convention set by
the iter-25/iter-26/iter-27 notes for prior ops-only iterations.

### Data-contract additions
None — this iteration introduces no new served field. `cache_size` is a performance-only tunable
already governed by `docs/goal.md`'s Constraints section ("Config-only thresholds"), not a Data
Contract value; the byte-identity spot-check exists specifically to prove no Data Contract value
moved.

## OUT OF SCOPE

- Any change to `pool_size`, `max_overflow`, `server.memory_cap_mb`, `malloc_arena_max`, or any
  other AG-10 host-guard value — only the owner may change these.
- Any code change to `app.engine.compass`, `build_manifest_payload`, `build_state_band`,
  `_derive_prospective_eligible`, `_severity_at`, `compass.vocabulary.direction_words`,
  `session_delta.py`, `compass.build_narrative`, `compass-whatchanged-card.tsx`,
  `compass-summary-card.tsx` — all binding "Do not redo" per the inlined iteration state.
- Any live `GET`/`POST /api/compass*` call outside the exact as-of set
  `{no param (2026-08-12), "2025-04-15", "1996-02-01"}` — no new manifest mint, no backfill of the
  16 word-less dates.
- Editing `journey-scripts/J-02.json` or `journey-scripts/J-03.json` after this iteration's replay
  lane runs them, regardless of pass/fail result.
- `_BarCache.prefill` re-bounding, the `next build` worker cap, or the `*_memory_pressure` test
  gating (goal.md Constraints (b)/(c)) — carried, not this iteration's build.
- Fixing or waiving `test_no_magic_numbers.py`'s pre-existing red failure — owner's call.
- The iteration-23 throw-away 7.8 GB copy deletion, `apps/frontend/.next-verify/` build-cache
  detracking, J-04's candidate-card screenshot retake, and J-05/J-06/J-08's recorded walkthroughs —
  all carried non-blocking items, none touched this round.

## DEFINITION OF DONE

- [ ] J-09's standing-warm VmPeak is re-measured cleanly with durable raw evidence saved to a file
      under `runs/goal-market-compass-iter-32/`, and the honest result (met or missed vs. 2.5 GB) is
      recorded in `reports/perf-budgets.md` and the dev handoff — never widened to force a pass.
- [ ] The concurrent-load check (burst at `server.limit_concurrency`=64) passes with zero
      `QueuePool` `TimeoutError`.
- [ ] The byte-identity spot-check shows no displayed value moved.
- [ ] `reports/perf-budgets.md` carries exactly one new dated addendum, appended (Addendum 40/41/42
      untouched).
- [ ] Required-still-passing journeys J-01 through J-08, J-10, J-11 remain green via deterministic
      replay; `J-02.json` and `J-03.json` execute for the first time since their iter-31 rewrite and
      their real pass/fail result is reported verbatim.
- [ ] No anti-goal violation introduced (AG-10's ceiling values untouched; AG-3/AG-8/AG-12 hold
      across the widened regression set).
- [ ] Unit tests pass (targeted, fixture-scoped only — never the full suite); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-32-dev.md`.

## TESTING REQUIREMENTS

- Browser: none new (J-09's Walkthrough is waived). Required-still-passing journeys J-01–J-08,
  J-10, J-11 are verified via deterministic replay (goldens in `journey-scripts/`), with J-02 and
  J-03 executing for the first time.
- Unit/integration: `test_sqlite_pragmas_applied_on_connect` (or equivalent) confirms `cache_size`
  still resolves to `-65536` from `config.yaml`; the fixture-scoped pytest subset touching
  `app/db.py` pragma application stays green (targeted run only, never the full suite per
  `docs/goal.md` Constraints).
- Error cases: N/A — no new user input surface. The only "failure" mode is the honest-miss path:
  if the ≤ 2.5 GB target is missed, the correct observable behavior is a plainly recorded honest
  figure and an explicit stop-for-owner-review statement, never a silently widened target or a
  fabricated pass.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line, numbered sequentially, of exactly this shape:

- TC-1: given `config.yaml`'s `database.pragmas.cache_size` already reads `-65536` (set at iter-4)
  and `pool_size`/`max_overflow` read `24`/`44`, when `git diff -- config.yaml` is inspected after
  this iteration, then it shows no change, or — if drift was found and corrected — shows only the
  single `cache_size` line differing with `pool_size`/`max_overflow` still `24`/`44`.
- TC-2: given a freshly started backend via `bash scripts/start-backend.sh` with nothing else of
  ours running on the host, when it reaches standing warm (readiness `ready`, VmPeak flat across
  ≥3 consecutive samples), then `/proc/<pid>/status` `VmPeak` is captured and every sample (not just
  the peak) is saved to a durable file under `runs/goal-market-compass-iter-32/` with UTC start and
  end capture timestamps.
- TC-3: given that raw capture, when the peak VmPeak value is compared to 2,621,440 kB (2.5 GB),
  then the dev handoff states the exact measured kB figure and whether it is ≤ or > the target,
  with the target value itself unchanged in `config.yaml`/`docs/goal.md` either way.
- TC-4: given the same running backend, when a request burst at `server.limit_concurrency` (64)
  concurrency is issued, then the burst completes with zero `QueuePool` `TimeoutError` and the
  pass/fail result is recorded in the new `reports/perf-budgets.md` addendum.
- TC-5: given a fixed already-manifested `as_of` from `{no param (2026-08-12), "2025-04-15",
  "1996-02-01"}`, when `GET /api/compass` (plus 1-2 other already-served read endpoints) is
  captured before and after this iteration's `cache_size` verification, then the response bytes
  are byte-identical, cited in the dev handoff.
- TC-6: given the re-measurement is complete, when `reports/perf-budgets.md` is inspected, then
  exactly one new dated addendum (next sequential number after the current highest) appears below
  the existing addenda, no existing addendum's text is edited or removed, and the new addendum
  cites the raw evidence file path from TC-2.
- TC-7: given `journey-scripts/J-02.json` and `journey-scripts/J-03.json` were rewritten at iter-31
  (mtimes 03:35:14 / 03:35:18) and have never been executed, when this iteration's deterministic
  replay lane runs with J-02 and J-03 included in Required-still-passing journeys, then
  `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` records an actually
  executed PASS or FAIL for each script (not a lint-only note), and neither script is edited again
  after that replay run regardless of the result.
- TC-8: given the widened Required-still-passing set (J-01, J-02, J-03, J-04, J-05, J-06, J-07,
  J-08, J-10, J-11), when the replay/browser-qa lane finishes, then all ten re-verify PASS with
  zero newly-failing or newly-regressed journeys, and any deviation from that is reported
  explicitly in the dev handoff rather than silently reconciled.

## NOTES

- Lesson applied (iter-31, ESCALATE): "any iteration about to record, carry, or act on a
  'waiting on the owner' blocker — open the underlying measurement and check whether primary
  evidence actually survives before treating the human as the only unblock path." Applied here:
  J-09 is planned as ordinary dev-owned re-measurement work, not an owner-gated wait.
- Lesson applied (iter-25, CONTINUE): "a perf addendum asserted a causal story... cross-check every
  causal and load claim against the server log and host-guard event stream, and retain the raw
  sampler output with UTC start/end times." Applied directly in the Backend scope's raw-evidence
  requirement above.
- Lessons applied (iter-29/iter-30/iter-31, all ESCALATE): "a golden written AFTER the replay lane
  ran is not coverage... bind [the hygiene rule] to ALL journeys in the run, not just the offending
  one." Applied by widening Required-still-passing to the full ten-journey passing set so J-02/J-03
  actually execute this round.
- Lesson applied (iter-27/iter-27b, CONTINUE): "a plain GET can write... the authorized-inputs list
  has to be stated to the lane that issues the requests, and every row-count claim must be
  re-derived AFTER the browsing lane finishes." Applied by naming the exact safe `as_of` set for
  every live `/api/compass` call this iteration, and by requiring a re-derived manifest-row-count
  check in the dev handoff (28 rows / 18 `as_of` / max id 28 expected unchanged).
- If the engine demotes this `Depth: full` spec to `lean` (as it has eight times previously this
  session), the dev handoff and the next evaluator MUST say so explicitly per `docs/goal.md`'s
  binding loop-mechanics rule — never silently treat `lean` output as satisfying a `full`
  requirement.
- Escalation note for the evaluator: if this clean re-measurement still misses the ≤ 2.5 GB target,
  that is the point where J-09's own "stop for owner review" clause genuinely fires (not before) —
  the evaluator should record the honest figure and surface the owner decision plainly rather than
  hold the iteration open pending a further re-measurement attempt.
