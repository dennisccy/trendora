# Goal Iteration 33 — Bound J-09's cold warm-up memory spike (Constraints c)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 33
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: `_BarCache`/`bar_cache`/`prefill`
  (`apps/backend/app/engine/prices.py`) is shared read infrastructure consumed by `regime.py`,
  `market_phase.py`, `sectors.py`, `themes.py`, `forward_testing.py` and the scanner's `run_scan`
  (via `apps/backend/app/engine/warmup.py:351`'s `with bar_cache(session):`) — far more than 3
  modules, none of which J-09's own acceptance steps (a memory metric only) test the correctness
  of. This exact cache already produced one real regression when bounded narrowly (iter-42's
  `expected_symbols` filter, reverted at iter-43 for a measured +5.1% whole-job memory cost) — a
  wrong bound here risks a silent AG-3 violation across virtually every other journey's displayed
  numbers. The evaluator's own binding depth recommendation for this iteration is also `full`,
  reinforcing rather than substituting for this structural justification.
- **Frontend Present:** no
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10, J-11
  (full regression widening — this iteration makes a real code change to shared architecture, not
  a zero-diff round like iter-32; see BACKGROUND)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
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
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*

## GOAL

Bind the ~1.29 GB, five-second start-up spike the iter-32 raw evidence pinned down in the
background warm-up's cold cadence-date compute to a size set in `config.yaml` (`docs/goal.md`
Constraints (c) — "AG-8 restored"), then re-measure the same way and record the honest result —
closing the last open acceptance gap in J-09, the sole remaining non-passing journey this session.

## BACKGROUND

iter-32 (CONTINUE) re-measured J-09 cleanly with durable raw evidence and still missed the target
(VmPeak 3,038,684 kB vs. 2,621,440 kB, +15.9%), but its own auditor read two extra columns
(`VmSize_kB`, `VmRSS_kB`) nobody had scored before: the peak is a boot transient reached at
**t+15.94s, ten seconds BEFORE readiness**, dropping to 1,750,504 kB by t+20.94s and settling at
1,298,796 kB virtual / 725,856 kB resident. `apps/backend/app/engine/warmup.py:351` opens
`with bar_cache(session):` around the cold cadence-date compute — an allocation of exactly that
shape and lifetime — which is precisely what `docs/goal.md` Constraints (c) already directs to be
"re-bounded to a configured memory budget (AG-8 restored)"; Constraints (a)/(b) from the same list
landed at iter-5. The inlined iteration-state "Do not redo" list is explicit: **"J-09's
re-measurement is DONE and must NOT be repeated as an iteration goal... Another measurement pass
closes nothing — only bounding the warm-up allocation can."** This iteration therefore makes a
real code change, not another measurement-only round.

**"Owner-only" is the wrong reading, already settled.** iter-32's dev handoff, QA report and
independent auditor all called Constraints (b)/(c) owner-gated; the iter-32 evaluator overruled
that in writing (assumption ledger, "iter-32 — goal-evaluator") because `docs/goal.md:2396-2400`
records the whole Host-resource-fit block as owner-authored **binding** work that "rides the
nearest applicable slices," not a permission to wait for. Do not re-record it as human-blocked.

**Safety catch, mandatory reading before any code change.** `docs/goal.md` Constraints (c) itself
says: "read the iter-43 handoff FIRST and preserve whatever correctness reason motivated its
unbounding; if that reason conflicts with the bound, stop and surface it for owner review instead
of guessing." That handoff is `docs/handoffs/goal-ops-hardening-iter-43-dev.md` (a prior session,
ops-hardening) — it reverted the LAST attempt to bound this exact cache's cold path: iter-42 added
a `WHERE symbol IN (expected_symbols)` filter to `_BarCache.prefill`, and the iter-42 auditor
re-measured its cost over the **whole job it runs inside** (not `prefill` in isolation) and found a
net **+5.1% peak-memory REGRESSION**, not the 2.5% reduction iter-42's own narrower measurement
claimed — because the ~36-43 excluded ETF/index/sector symbols (SPY, QQQ, the XL* SPDRs, `^VIX`,
etc., read by `regime.py`/`market_phase.py`/`sectors.py`/`themes.py` on every snapshot date) fell
back to the costlier per-symbol `list[Bar]` lazy-load path instead of the compact array-based
`_SymbolColumns` format the eager scan produces (`prices.py:211-259`, iter-41 B5). Whatever
mechanism this iteration chooses to bound the warm-up's cold path, **its cost must be measured
over the whole warm-up job, never the cache-load step in isolation** — that is the exact narrow-
measurement mistake that produced the iter-42/43 regression-and-revert cycle. Note also:
`warmup.py`'s `with bar_cache(session):` (unlike `prefilled_bar_cache`) never calls `.prefill()`
explicitly today — every symbol the cadence loop touches is lazy-loaded through the SAME costlier
`list[Bar]` path `prefill`'s eager scan exists to avoid, which is itself worth investigating as
part of understanding where the 1.29 GB actually accumulates.

Depth is `full` under Trigger 1 (see metadata) — a real code change to shared bar-loading
infrastructure this session has already regressed once. Required-still-passing is widened to the
full ten-journey passing set (unlike iter-32's zero-diff round) because this change touches code
every other journey's numbers indirectly depend on.

**Three repair items ride along, all mechanical, per iter-32's explicit recommendation and its own
"pipeline honesty findings":** (1) the deterministic replay lane has now been run without
`--results` for five consecutive rounds, letting two gates (reviewer, QA) certify a results file
that did not exist at signoff time — this iteration's replay invocation MUST pass `--results
<path>` and must fail (not silently succeed) when that file is absent/empty afterward; (2) merge
the replay lane's real PASS/FAIL rows into the merged `ui-test-results.md` file instead of leaving
covered journeys recorded SKIPPED; (3) `reports/perf-budgets.md` Addendum 43 still carries an
uncorrected wrong sentence about which `as_of` values were requested (the auditor fixed the same
sentence in the dev handoff but not here) — append a dated correction note (Addendum 43's own text
stays untouched, append-only).

**As-of contradiction closed.** The "Do not redo" list flags that iter-32's spec forbade calls its
own TC-7 mandated (it restricted live `as_of` values to a 3-value safe set while requiring replay
of goldens that visit 4 different dates). This spec instead authorizes the exact union every one
of the ten stored goldens actually uses, confirmed by reading each `journey-scripts/*.json`
directly: **`{no param / frontier "2026-08-12", "1996-02-01", "2025-04-15", "2026-03-30",
"2026-07-23", "2026-08-03", "2026-08-11"}`** — 7 distinct values. All 7 are already among the 18
distinct `as_of` values stored in `next_session_manifests` (re-derived read-only at iter-32), so no
call at any of them can mint a new manifest row regardless of how many times it is issued.

**Host safety note for the human operator (plain prose — this is not a destructive migration or a
damaged-data repair, so neither `Depth enforcement: required` nor `Maintenance isolation: required`
applies; the measurement needs the backend booted, which `Maintenance isolation` would block):**
this iteration touches the single heaviest-memory code path in the backend, on the 26.7 GB host a
goal-mode run froze via swap-thrash on 2026-08-20. Nothing else of ours — in particular no sibling
`tensteps` goal-mode session — should be running while the standing-warm measurement executes.
iter-32's own measurement ran WHILE a `tensteps` process was active and got lucky (the contention
did not move the conclusion); do not rely on that again.

`test_no_magic_numbers.py`'s pre-existing red failure on three untouched files
(`indicators.py`/`forward_testing.py`/`research.py`) remains out of scope (owner's call).

## IN SCOPE

### Backend
- [ ] Read `docs/handoffs/goal-ops-hardening-iter-43-dev.md` and `prices.py:211-259`'s iter-41/42/43
      docstring paragraphs FIRST, before any change to `_BarCache`/`bar_cache`/`prefill` or
      `warmup.py`'s cadence loop — preserve the correctness reason recorded there.
- [ ] Bound the cold cadence-date allocation `apps/backend/app/engine/warmup.py:351`'s
      `with bar_cache(session):` block produces (`apps/backend/app/engine/prices.py`'s
      `_BarCache`/`bar_cache`/`prefill`, and/or the warm-up cadence loop's own consumption pattern)
      to a size set under `config.yaml` (a new key under `compass.*` or `startup.*`, per Constraints
      (c) — "re-bounded to a configured memory budget, AG-8 restored"). The chosen mechanism must
      NOT reproduce the iter-42-class regression (a bound whose cost, measured over the WHOLE
      warm-up job, is net negative) — whatever is built must be measured that way, not on the
      cache-load step in isolation.
- [ ] Safety catch (Constraints (c), verbatim): if no bound can be applied without either (a)
      reproducing/worsening a memory or latency regression measured over the whole warm-up job, or
      (b) changing any served value, STOP implementation, record the conflict plainly in the dev
      handoff, and leave the honest unbounded figure standing — do not guess, do not ship a change
      that trades a memory miss for a new correctness or performance regression.
- [ ] Any new numeric threshold this introduces is config-only (no magic numbers); if `warmup.py`
      gains a new config-sourced literal, register it in `test_no_magic_numbers.py`'s `CALC_FILES`
      alongside the existing `prices.py` entry.
- [ ] Re-run the standing-warm measurement on a fresh `bash scripts/start-backend.sh` boot with
      nothing else of ours running (see host-safety note above); save the full raw per-second
      `/proc/<pid>/status` capture (`VmPeak_kB`, `VmSize_kB`, `VmRSS_kB`, every sample, UTC
      start/end timestamps) to a durable file under `runs/goal-market-compass-iter-33/`.
- [ ] Re-run the iter-71-class concurrent-load burst check (`server.limit_concurrency`) against the
      same backend; record pass/fail (zero `QueuePool` `TimeoutError`).
- [ ] Byte-identity spot-check: capture `GET /api/compass` (plus 1-2 other already-served read
      endpoints) across the authorized 7-value as-of set (see BACKGROUND) before and after the code
      change; cite the result in the dev handoff.
- [ ] Append ONE new dated addendum (Addendum 44 — the next sequential number after Addendum 43) to
      `reports/perf-budgets.md`, recording: the new measured VmPeak/VmSize/VmRSS figures (at peak,
      at t+20s, and end-of-window), the comparison to the 2,621,440 kB target and to the iter-4 /
      iter-25 / iter-32 prior figures, the concurrent-load result, the byte-identity result, and the
      raw-evidence file path with its UTC capture window.
- [ ] If the ≤ 2.5 GB target is still missed after this genuine bounding attempt (or the safety
      catch fired): record the honest figure, do NOT widen the target, and state plainly in the dev
      handoff that owner review is the remaining path — never fabricate or round a passing number.
- [ ] Repair item 1: invoke the deterministic replay lane WITH `--results
      reports/phase-goal-market-compass-iter-33-regression-replay-results.md`; treat a missing or
      empty results file after the run as a lane failure, not a silent success.
- [ ] Repair item 2: merge the replay lane's actual PASS/FAIL rows into
      `reports/phase-goal-market-compass-iter-33-ui-test-results.md` so no journey the replay lane
      covered is left recorded SKIPPED.
- [ ] Repair item 3: append a dated correction note to `reports/perf-budgets.md` fixing the "no
      `as_of` outside this 3-value set was requested" sentence still standing in Addendum 43 (state
      the true combined-backend-instance scope) — Addendum 43's original text stays untouched,
      append-only.

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
None visible to a user; `reports/perf-budgets.md` gains one dated addendum plus one dated
correction note (both internal ops reports, outside the product's Information Architecture).

### Blueprint conformance
No new surfaces — J-09 touches no page in the Information Architecture; `blueprint.md` gets an
informational iter-33 note only (no IA or Data Contract row changes), matching the convention set
by the iter-25/26/27/32 notes for prior ops-only iterations.

### Data-contract additions
None — this iteration introduces no new served field. The new memory-budget config key is a
performance-only tunable already governed by `docs/goal.md`'s Constraints section ("Config-only
thresholds"), not a Data Contract value; the byte-identity spot-check exists specifically to prove
no Data Contract value moved.

## OUT OF SCOPE

- Any change to `pool_size`, `max_overflow`, `server.memory_cap_mb`, `malloc_arena_max`, or any
  other AG-10 host-guard value — only the owner may change these.
- Reintroducing the iter-42 `WHERE symbol IN (expected_symbols)` filter unchanged/as-is — already
  proven a net whole-job regression at iter-43.
- Any code change to `app.engine.compass`, `build_manifest_payload`, `build_state_band`,
  `_derive_prospective_eligible`, `_severity_at`, `compass.vocabulary.direction_words`,
  `session_delta.py`, `compass.build_narrative`, `compass-whatchanged-card.tsx`,
  `compass-summary-card.tsx` — all binding "Do not redo" per the inlined iteration state.
- Any live `GET`/`POST /api/compass*` call outside the authorized 7-value as-of set in BACKGROUND —
  no new manifest mint, no backfill of the remaining word-less dates.
- Editing any of the ten `journey-scripts/*.json` goldens after this iteration's replay lane runs
  them, regardless of pass/fail result.
- The `next build` worker cap and `*_memory_pressure` test gating (Constraints (a)/(b)) — already
  landed at iter-5, not this iteration's build.
- Fixing or waiving `test_no_magic_numbers.py`'s pre-existing red failure — owner's call.
- Destructive-drill isolation infrastructure — explicitly out of scope per `docs/goal.md` Constraints.
- The nine carried non-blocking items (J-04's candidate-card screenshot retake; J-02/J-03/J-05/
  J-06/J-08's recorded walkthroughs; the pre-existing `test_no_magic_numbers.py` red failure; the
  "What changed"/"Leadership rotation" identical-rows note; the iteration-23 throwaway 7.8 GB copy;
  `apps/frontend/.next-verify/` build-cache tracking; J-01's automatic re-check wording; the
  `browser_checks_run` bookkeeping mismatch; the five older owner questions) — untouched this round.

## DEFINITION OF DONE

- [ ] J-09's cold warm-up allocation is bounded via a config-only budget (or the safety-catch STOP
      is invoked and documented plainly), and the new standing-warm VmPeak is re-measured with
      durable raw evidence; the honest result (met or missed vs. 2.5 GB) is recorded in
      `reports/perf-budgets.md` and the dev handoff — never widened to force a pass.
- [ ] The concurrent-load check (burst at `server.limit_concurrency`) passes with zero `QueuePool`
      `TimeoutError`.
- [ ] The byte-identity spot-check across the authorized 7-value as-of set shows no displayed value
      moved.
- [ ] `reports/perf-budgets.md` carries exactly one new dated addendum (Addendum 44, append-only)
      plus one dated correction note fixing Addendum 43's wrong sentence — no existing addendum
      text edited or removed.
- [ ] Required-still-passing journeys J-01 through J-08, J-10, J-11 remain green via deterministic
      replay, with all ten goldens actually executed and their real results merged into the
      `ui-test-results.md` file (none left recorded SKIPPED when the replay lane covered them).
- [ ] No anti-goal violation introduced (AG-3, AG-8, AG-9, AG-10, AG-12 hold across the widened
      regression set).
- [ ] Unit tests pass (targeted, fixture-scoped only — never the full suite); `test_bar_cache.py`'s
      existing B1/B5/B6 regression + byte-identity oracles stay green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-33-dev.md`.

## TESTING REQUIREMENTS

- Browser: none new (J-09's Walkthrough is waived). Required-still-passing journeys J-01–J-08,
  J-10, J-11 verified via deterministic replay across their existing goldens (`journey-scripts/`).
- Unit/integration: targeted `test_bar_cache.py` (existing B1/B5/B6 regression + iter-43
  byte-identity oracles) plus any new test proving the new bound's behavior and its whole-job cost;
  if `warmup.py` gains a config-sourced literal, confirm the targeted `test_no_magic_numbers.py`
  subset covering the touched files is green.
- Error cases: N/A — no new user input surface. The only "failure" mode is the honest-miss / safety-
  catch path: if bounding would break correctness, or the target is still missed after a genuine
  attempt, the correct observable behavior is a plainly recorded honest figure and explicit
  stop-for-owner-review statement in the dev handoff, never a fabricated pass or a silently widened
  target.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line, numbered sequentially, of exactly this shape:

- TC-1: given `docs/handoffs/goal-ops-hardening-iter-43-dev.md` and `prices.py:245-259`'s iter-43
  docstring paragraph, when the developer designs the new bound, then the dev handoff cites both
  and states explicitly, with a measured number, why the chosen mechanism does not reproduce the
  documented +5.1% whole-job regression.
- TC-2: given the bounded code deployed and a backend started fresh via `scripts/start-backend.sh`
  with nothing else of ours running, when the standing-warm measurement runs, then a raw per-second
  CSV (`VmPeak_kB`, `VmSize_kB`, `VmRSS_kB`, UTC start/end) is saved under
  `runs/goal-market-compass-iter-33/` and its max `VmPeak_kB` is read directly from the file.
- TC-3: given that CSV, when the max `VmPeak_kB` value is compared to 2,621,440 kB, then the dev
  handoff and `reports/perf-budgets.md`'s new Addendum 44 both state the exact measured kB figure
  and whether it is ≤ or > the target, with the target value itself unchanged in
  `config.yaml`/`docs/goal.md` either way.
- TC-4: given the bounded backend running, when a request burst at `server.limit_concurrency` (64)
  is issued, then the burst completes with zero `QueuePool` `TimeoutError` lines in the backend log
  segment, recorded in Addendum 44.
- TC-5: given the authorized as-of set `{no param (frontier, "2026-08-12"), "1996-02-01",
  "2025-04-15", "2026-03-30", "2026-07-23", "2026-08-03", "2026-08-11"}`, when `GET /api/compass`
  (plus 1-2 other already-served endpoints) is captured before and after the code change for each
  value, then the response bytes are byte-identical, cited in the dev handoff.
- TC-6: given the change is complete, when `next_session_manifests` row count / distinct `as_of`
  count / max id are read before and after the iteration, then all three are unchanged (zero new
  mints, zero mutations).
- TC-7: given the deterministic replay lane is invoked with `--results
  reports/phase-goal-market-compass-iter-33-regression-replay-results.md`, when the lane completes,
  then that file exists, is non-empty, and lists an actually-executed PASS/FAIL row for each of the
  ten Required-still-passing journeys (not a lint-only note).
- TC-8: given that results file, when `reports/phase-goal-market-compass-iter-33-ui-test-results.md`
  is generated, then no journey the replay lane covered is left recorded SKIPPED — the replay
  result is merged in verbatim.
- TC-9: given `reports/perf-budgets.md` Addendum 43's uncorrected "no `as_of` outside this 3-value
  set was requested" sentence, when this iteration's addendum work runs, then a dated correction
  note is appended after Addendum 43 (its original text untouched) stating the true combined-
  backend-instance scope.
- TC-10: given the bound cannot be implemented without breaking correctness or reproducing a
  whole-job regression, when the developer discovers this during implementation, then work STOPS,
  the conflict is recorded plainly in the dev handoff, the honest re-measured figure is what J-09
  carries forward, and no target line in `config.yaml`/`docs/goal.md` is moved.

## NOTES

- Lesson applied (iter-32, CONTINUE, first lesson): "a perf measurement's *other columns* are where
  the answer hides... always plot the neighbouring columns before concluding 'the footprint is X'."
  Applied by requiring `VmSize_kB`/`VmRSS_kB` alongside `VmPeak_kB` in every raw capture and in
  Addendum 44 (TC-2/TC-3).
- Lesson applied (iter-32, CONTINUE, second lesson): "'Owner-authored' is not 'owner-gated'... Open
  the constraint's own text before recording it as a human-owned blocker." Applied throughout —
  this spec plans Constraints (c) as ordinary scheduled dev work, not an owner-gated wait.
- Lesson applied (iter-32, CONTINUE, third lesson): "a gate that asserts an artifact without opening
  it is indistinguishable from a gate that read it, right up until the claim is false." Applied via
  repair item 1 / TC-7 — the replay lane must be invoked with `--results` and must fail when the
  file is missing, closing a five-round-old defect family.
- Lessons applied (iter-29/30/31, all ESCALATE): "a golden written AFTER the replay lane ran is not
  coverage... bind [the hygiene rule] to ALL journeys in the run, not just the offending one."
  Applied by widening Required-still-passing to the full ten-journey passing set and forbidding any
  edit to a golden after this iteration's replay lane executes it (OUT OF SCOPE).
- If the engine demotes this `Depth: full` spec to `lean`, the dev handoff and the next evaluator
  MUST say so explicitly per `docs/goal.md`'s binding loop-mechanics rule ("`Depth: full` must
  never silently become `lean`") — never silently treat `lean` output as satisfying a `full`
  requirement. iter-32 held `full` for the first time in a while; do not assume this round will.
- Escalation note for the evaluator: iter-32 already recorded two non-blocking owner decisions —
  (a) accept the honest worst-moment figure since serving-time RSS (725,856 kB) comfortably fits
  two backends on this host, closing J-09 as-is; (b) if the owner would rather nobody touch
  warm-up code, (a) becomes the only path. If this iteration's genuine bounding attempt still
  misses the target, or the safety catch fires, present those same two owner decisions again
  plainly rather than planning a further unbounded engineering attempt without a ruling.
