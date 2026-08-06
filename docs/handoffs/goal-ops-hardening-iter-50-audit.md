# goal-ops-hardening-iter-50 Audit Report

**Date:** 2026-08-06
**Auditor:** Hard audit pass — skeptical, evidence-based (third audit pass this iteration)

---

## 1. Executive Verdict

**Verdict:** FAIL

The engineering landed this round is real and materially stronger than what it replaced — the columnar
accumulators moved the crash frame's peak from 7.76 GB to 3.13 GB (61.8 % margin under the 8192 MB cap),
and the TC-1 scenario finally ran **as written** with 1,179/1,179 health polls answering HTTP 200 and zero
uncaught `MemoryError` (verified by me in the raw evidence file, not the handoff). But the phase's own GOAL
has two clauses and only the first is proven: **J-05's defining case still has no in-product proof**, and
the iteration's top-priority DEFINITION OF DONE item — J-07 passing with the ≤2 s health ceiling honored —
is **refuted by the round's own best measurement** (96 of 1,179 polls exceeded 2.0 s, worst 10.063 s), a
result no lane re-run can convert into a pass. On top of that, DoD item 4 (J-04 has no executed row
anywhere) and DoD item 7 (the lane ran *before* two product-code passes) are unmet, and the artifact that
certifies the round — `reports/qa/goal-ops-hardening-iter-50-qa.md` — returns `Verdict: PASS` while
asserting a browser-lane re-run that never happened.

I applied one surgical product-code fix: the B4 memory-pressure cooldown was **bypassed on the
single-flight waiter path**, so an already-waiting caller still started its own full-scale compute inside a
memory-exhausted process — the exact amplification the cooldown exists to stop, on the exact path the
2026-08-05 outage took. Proven by a new regression test that fails without the fix.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the memory-pressure cooldown never covered the single-flight WAITER, the path the outage actually took**

`apps/backend/app/engine/research.py:3832` (top-of-function cooldown check) vs `:3849-3878` (the waiter
fall-through, pre-fix). The iteration's own B4 termination condition is checked only **before** a caller
registers in the single-flight registry. A caller that was **already waiting** when the owner degrades
wakes on the owner's `finally`, re-checks `_cached_row()` — which is `None` *by construction*, because the
same fix deliberately never persists a degraded payload (`research.py:3900-3922`) — and then fell straight
through to `compute_factor_lab_all` and started its own full-scale multi-GB compute in the process that had
just run out of memory.

This is not hypothetical: the developer's own rationale for re-basing the wait ceiling cites
`logs/backend.log` recording **five waiters falling through in 2m16s during the 2026-08-05 outage window,
each starting an additional independent compute** (`research.py:3722-3731`). The cooldown was added to stop
exactly that, and it stopped it only for callers arriving *after* the degrade.

I reproduced it before touching anything: the new test failed against the shipped code with the log line
`factor_lab_all single-flight wait elapsed or owner failed … computing independently (duplicate compute
possible)` firing immediately and the heavy-read spy counting **2** computes.

**Fix applied** (`research.py:3854-3871`): after the bounded wait and the cache re-check, consult
`_degraded_cooldown_get(key)` and serve the owner's honest degraded payload rather than starting a second
compute. Non-degrading owner failures are unaffected (no cooldown entry exists, so the existing
compute-independently fallback still runs — proven by
`test_factor_lab_all_cached_waiter_does_not_deadlock_when_owner_raises` still passing).

I weighed CRITICAL and chose IMPORTANT: the columnar rewrite (B3 of the previous audit) makes the degrade
trigger far rarer — the live drill peaked at 3.13 GB against an 8192 MB cap — so this is now the second-order
amplification path rather than the primary crash mechanism.

**B2 — IMPORTANT (gap, not fixed — spec-internal conflict): the interlock can drop the ingest finalize tail's drawdown warm for a whole dataset version**

`apps/backend/app/engine/data_manager.py:4290` and `apps/backend/app/engine/warmup.py:202-232`.

Reachable ordering, entirely realistic in this session's own lanes (a backfill started while the boot
re-warm is still running):

1. The boot re-warm wins the narrow slot (`warmup.py:208`) and enters its multi-minute per-claim loop.
2. An ingest job starts; `_enter_ingest_heavy_warm` opens the window; its `drawdown_expectations_warm`
   phase calls `_try_acquire_drawdown_warm("ingest_finalize")` (`data_manager.py:4290`), finds the slot
   held, and **defers the whole phase** — `drawdown_warmed` stays False and `drawdown_expectations` is
   honestly omitted from `aggregates_refreshed`.
3. The boot re-warm's next per-claim check sees the ingest window open (`warmup.py:228`) and **breaks out**
   of its own loop.

Neither side completes for the **new** dataset version the ingest just created, so every
drawdown-expectations claim is cold under the current stamp. The ingest side's "next natural trigger" is
the *next ingest job*; the boot side's is the *next restart* — so for this dataset version the work is
effectively dropped, and the cost lands on the next `/evidence` view as a cold compute on a request path
(worst observed single claim: the ~250 s `combination:composite:h20`). That is precisely the pattern
J-05/J-08 exist to eliminate.

Not fixed deliberately. The phase spec contradicts itself here: TESTING REQUIREMENTS says *"a warm that
defers under the new guard must resume on its own next natural trigger, never silently drop the work"*,
while TC-5 requires *"the finalize-tail warm defers analogously"*. The implementation follows TC-5
literally. Per `.claude/judgment-rubrics.md` §3, two legitimate readings of the spec that change product
behavior are an owner decision, not an auditor's unilateral redesign. The narrow fix, if the owner wants it,
is to let the finalize tail **bounded-wait** for the slot instead of deferring — the boot re-warm releases
within one claim once the ingest window is open — which would also need TC-5's wording amended.

Disclosed by the developer as carried finding B5; no test covers this specific double-skip ordering (the
four new interlock tests cover defer-for-the-window, mid-loop yield, window span, and depth unwind).

**B3 — GAP (carried): the re-based 2,625 s single-flight ceiling trades a proven amplification for an unmeasured thread-hold**

`apps/backend/app/engine/research.py:3732` (`_FACTOR_LAB_ALL_MEASURED_COLD_MISS_S = 875`) and the waiter at
`:3850`. A waiter now occupies an anyio threadpool worker for up to 43 minutes instead of 15. With
`--limit-concurrency 64` and the default threadpool width, enough concurrent Factor Lab viewers could starve
every other endpoint — including `/api/health`, the very thing J-07 measures. The live drill had a single
caller, so the waiter regime remains unmeasured. Correctly scoped by the previous audit to the next round's
measurement plan; B1's fix above reduces (but does not remove) the population that can reach it, since a
degraded owner now releases its waiters immediately with a payload instead of leaving them to compute.

**B4 — OBSERVATION (carried): the AG-8 disclosure net still never fires before the allocation it pre-announces**

`config.yaml:915` (`factor_pool_max_observations: 2000000`) is checked after the sweep that would exhaust
memory, and it wants re-tuning against the columnar footprint. `config.yaml` is an AG-10 frozen file — an
owner change, not an agent one. Pre-existing since iter-31.

### Test Findings

**T1 — CRITICAL (not fixed, deliberately): the QA report certifies a re-run that never happened**

`reports/qa/goal-ops-hardening-iter-50-qa.md:1` returns `Verdict: PASS`; `:7` and `:15` state it is
"REGENERATED … reflects fresh evidence from the re-run"; `:118-124` then admit the full 8-journey lane is
"deferred to the browser-qa-agent lane". Three independent artifacts contradict it:

- `reports/phase-goal-ops-hardening-iter-50-ui-test-results.md` (written 00:12, i.e. **before both
  audit-fix passes**) records **Browser QA Verdict: FAIL** — UT-03 a 12m03s+ total outage, `UT-J-04`
  missing, and `UT-J-05` / `UT-J-06` / `UT-J-07` (all three **target** journeys) with no executed row.
- `runs/goal-ops-hardening-iter-50/status.json:41-44` records `browser_checks_run: false` and
  `qa_verdict: "INVALID_PENDING_REGENERATION"`.
- My own run: `tests/test_factor_lab_all.py` collects **33** tests (`33 passed in 52.82s`), while the QA
  report cites `28 passed in 52.15s` as its fresh evidence — the report was generated against code that is
  now two product-code passes stale.

Not fixed: the phase spec's NOTES make regeneration from the re-run the only permitted remedy and
hand-correcting the verdict the prohibited act (the iter-49 contradiction this iteration is bound not to
repeat). The machine-readable state in `status.json` is honest; the human-readable QA artifact is not, and
anything downstream that parses the QA verdict line will read a false PASS.

**T2 — IMPORTANT: DoD items 1, 2, 4 and 7 are unmet; item 1 is refuted, not merely unevidenced**

| DoD item | State | Evidence |
|---|---|---|
| 1. J-07 passes, health poll ≤2 s, zero non-200 | **Refuted** | 96/1,179 polls > 2.0 s, worst 10.063 s (`iter50-auditfix2-tc1-live-drill.json` → `health.polls_over_2s`, `health.latency_max_s`; `perf-budgets.md` Addendum 10). No `UT-J-07` row in any lane. A lane re-run cannot change this — the cause is GIL contention, not memory |
| 2. J-05 moves on real **in-app** lane evidence | **Unmet** | The TC-1 drill is API-level (`POST /api/data/jobs`) and the developer says so: "TC-10/TC-11's in-app UI half is the lane's, not this drill's". The lane's UT-02 ran on pre-fix code and captured **no** `/scanner-runs` leaderboard screenshot; the rewritten `J-05.json` golden has never been executed |
| 3. J-06 Factor Lab load measured + recorded | **Met (warm)** | `perf-budgets.md` Addenda 8-10; warm 52 ms nav / 163 ms API, repeat 43 ms. See the GAP note below on the cold path |
| 4. J-01/J-03/J-04/J-08/J-09 each a real executed row | **Unmet** | `ui-test-results.md` "Missing Required Journeys": `UT-J-04` — no test case executed by any lane. J-01/03/08/09 have PASS rows |
| 7. Lane runs LAST, no product-code change after | **Unmet** | Lane 00:12 → fix pass 1 (research/data_manager/warmup, ~02:45-04:23) → fix pass 2 (research/data_manager + J-05 golden, ~05:41-06:51) → **this audit's B1 fix** |

DoD items 5 (no AG-10 cap change — `git diff` over the four frozen files is empty, re-verified by me), 6
(unit tests + byte-identity) and 8 (handoff) are met.

**T3 — OBSERVATION (positive, verified not assumed): the unit-level evidence is genuinely strong**

I re-ran, in this checkout: `tests/test_factor_lab_all.py` → **34 passed in 53.89s** (33 pre-existing + my
new regression test), and `tests/test_research_streaming.py -k "factor_lab or cooldown or degrad or
single_flight or pinned"` → **18 passed in 3.19s**, including both pinned byte-identity oracles. I also read
the oracles rather than trusting their names: `test_shared_pools_chunked_equal_the_pinned_unchunked_
reference` (`tests/test_factor_lab_all.py:480`) compares the columnar accumulators against
`_all_pools_reference_unchunked` (`:391`), an independently written pre-columnar implementation — so AG-3
byte-identity for the columnar rewrite is proven by data comparison, not by construction alone. Note that
the TC-3 oracle (`tests/test_research_streaming.py:623`) calls the *current* shared-pool builder, so it
pins only the per-(factor,horizon) transient; the columnar proof rests on the `test_factor_lab_all.py` one.

**T4 — OBSERVATION (not independently verified): the pre-existing `test_warmup.py` failure**

`test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns` is reported failing
identically at `HEAD` with this iteration's changes stashed. I did not re-run it (20+ min) and did not
re-stash; the claim is plausible on code reading (the interlock only defers the drawdown warm, which is not
what that test counts) but stands on the developer's evidence, not mine.

---

## 3. Domain Assessment

The core domain work is sound, and I checked it at code level rather than accepting the handoff:

- **The columnar accumulators are a genuine representation redesign, not a constant-factor dodge.**
  `_FactorCoreRecords` / `_FactorObsPool` (`research.py:882-1030`) carry `None` in a 1-byte presence mask —
  never a `0.0` or NaN sentinel — and both implement the sequence protocol so every existing caller, oracle
  and test still sees the historical tuple shape. `compute_factor_lab_all`'s hot loop reads the columns
  directly (`:1298-1315`), so the hot path allocates nothing per pool row.
- **The B4 `float(v)` coercion at the append site is the right call and is where the old consumer's
  coercion always was.** `"3.5" → 3.5`, `3 → 3.0`, `True → 1.0` all serve byte-identically; a genuinely
  non-numeric `record_json` raw is now excluded as a factor-NULL with a counted AG-8 WARNING instead of
  raising `TypeError` out of the shared pool builder (where nothing would have caught it and the whole
  `?all=true` response would have 500'd).
- **The `phase_context_by_date` skip is a faithful mirror, not an approximation.**
  `_drawdown_expectations_ledger_needs_recompute` (`data_manager.py:3889-3919`) uses the same
  `_dataset_version`, the same `underwater_horizons` scope gate and the same
  `(subject, view, asof_key, dataset_version, horizon)` lookup that
  `forward_testing.compute_drawdown_expectations_cached` (`forward_testing.py:2592-2614`) performs, and that
  function caches `None` results too — so an honestly-unresolvable claim reads as a HIT on both sides. A
  divergence in the conservative direction only costs the per-claim fallback, which is byte-identical.
- **The interlock's control flow is balanced.** `_enter_ingest_heavy_warm` is paired with
  `_exit_ingest_heavy_warm` in the finalize tail's `finally` (`data_manager.py:4015`, `:4440`), the depth
  counter is clamped at zero, and every `warmup.py` exit path releases the narrow slot. The functional hole
  is a policy question (B2), not a leak.
- **Disclosure quality is the best this session has produced.** `perf-budgets.md` Addendum 10 states
  plainly that TC-7 is not met, that the wedge class is `unproven-either-way`, and that Addendum 9's
  "TC-1 met live" claim is withdrawn — with an additive dated CORRECTION rather than a rewrite. The
  `status.json` blockers say the same. That honesty is why this audit could go straight to the code instead
  of re-litigating claims.

Where the product still stands apart from the code: `/research/factor-lab` recomputes on the request path
after every ingest (the dataset-version stamp changes, so the next view is a guaranteed MISS costing
578-875 s). This iteration made that path *survivable* — bounded, isolated, single-flighted, cooled down —
but not *fast*, and `docs/goal.md`'s own compute-at-ingest principle prescribes the structural fix the
developer names: serve this view from an ingest-time artifact.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/research.py` (`:3854-3871`) | Re-check the memory-pressure cooldown after the single-flight wait, so an already-waiting caller is served the owner's honest degraded payload instead of starting a second full-scale compute in a memory-exhausted process |
| 2 | — (proof for #1) | `apps/backend/tests/test_factor_lab_all.py` (`:888-967`, added by this audit) | `test_already_waiting_caller_is_served_the_cooldown_not_a_second_doomed_compute` — counting spy on the heavy read; asserts the waiter entered *before* the owner degraded (so the run is not vacuously served by the top-of-function check) and that exactly **1** compute was attempted |

**Post-fix verification (evidence, not assertion):**

1. Before the fix: `pytest tests/test_factor_lab_all.py -k already_waiting` → **1 failed**, spy count 2, with
   `factor_lab_all single-flight wait elapsed or owner failed … computing independently` in the captured log.
2. After the fix: `pytest tests/test_factor_lab_all.py -q -p no:randomly` → **34 passed in 53.89s** (the
   whole module, including `test_factor_lab_all_cached_waiter_does_not_deadlock_when_owner_raises`, which
   pins that a *non*-degrading owner failure still falls through to an independent compute).
3. Regression on the touched paths: `pytest tests/test_research_streaming.py -k "factor_lab or cooldown or
   degrad or single_flight or pinned"` → **18 passed in 3.19s**, both pinned byte-identity oracles green.
4. Diff scope re-read: the product change is one guarded early return inside the existing `if not is_owner`
   block plus its comment; no other statement, signature or constant changed. Frozen AG-10 files re-checked
   after the edit — `git diff` over `config.yaml`, `project-extensions/host-guard/host-guard.env`,
   `scripts/start-backend.sh`, `scripts/dev.sh` is empty.

**TC-13 consequence, stated plainly:** this fix touches product code. The full 8-journey browser/replay lane
re-run was **already** a hard blocker before it (`status.json:9`) because the lane has never run against
this iteration's code, so nothing here worsens the sequencing — but the re-run now covers this change too,
and `reports/qa/goal-ops-hardening-iter-50-qa.md` must be **regenerated** from that run, never hand-edited.

---

## 5. Recommended Next Step

Do **not** close iter-50 on the current artifacts. In order:

1. **Run the full 8-journey browser/replay lane against the current code, last** — including the rewritten
   `J-05.json` golden (target `2010-11-08`, live-confirmed at 0 snapshot rows; verify again immediately
   before the run) — and **regenerate** the QA report from that run. This is the only thing that can close
   DoD items 2, 4 and 7 and retire T1. No product-code change may follow it.
2. **Score J-07 honestly as still failing.** DoD item 1 is refuted by measurement, not missing evidence: the
   ≤2 s ceiling breaches under exactly the concurrency TC-1 demands, and the cause (GIL contention between
   two CPU-bound Python computes in one process) is untouched by any memory bound. Rounding it up on a
   lane re-run would be the renegotiation `.claude/judgment-rubrics.md` §4 names.
3. **Make the next iteration's one risky change the structural one J-07 step 2 actually needs** — take the
   `/research/factor-lab` compute off the request path (an ingest-time artifact per `docs/goal.md`'s
   compute-at-ingest principle, or off the event loop) — rather than another memory-side fix. That single
   change is also what retires the cold-page-load problem and shrinks B3's waiter population to zero.
4. **Put B2 to the owner as a spec question**, not to a developer as a bug: TESTING REQUIREMENTS' "never
   silently drop the work" and TC-5's "the finalize-tail warm defers analogously" cannot both hold. If the
   finalize tail is the priority producer (as the code's own comment argues), it should bounded-wait for the
   narrow slot rather than defer, and TC-5's wording should follow.
5. Carry B3 (waiter thread-hold, unmeasured) and B4 (`factor_pool_max_observations` re-tune, a frozen-file
   owner change) as recorded, unfixed limitations.
