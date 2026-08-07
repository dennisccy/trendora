# goal-ops-hardening-iter-51 Audit Report

**Date:** 2026-08-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's actual deliverable — the Factor Lab's default all-history view served from an
ingest-time artifact instead of a request-path compute — is implemented correctly and proven in the
running product, not just in unit tests. I verified it independently rather than trusting the
handoff: the live DB carries exactly one `__all_factors__` cache row at the CURRENT dataset-version
stamp (`r2913-f6502520-allh-mdd-v1`, `asof_key='all'`, `horizon=20`, written 00:27:47 during job
id=325), and the browser lane measured `GET /api/research/factor-lab?all=true` at **0.0078s** against
the 578–875s pre-iteration cold compute. The `_combination_cohort_members` bound is a genuine pure
allocation-strategy change (byte-identical against a pinned oracle; I confirmed the monkeypatch proof
is not vacuous).

The gaps are in **verification, not in the code**. The DoD line "TC-1 through TC-9 all pass" is false
as written: TC-5's "zero non-200s, zero connection failures" was breached in both live drills
(9/653 solo, 19/892 concurrent), TC-6's mid-warm cache HIT did not occur (the concurrent request
became the single-flight owner and paid the full compute), TC-3's browser measurement was never
recorded in `reports/perf-budgets.md`, and the browser/replay lane returned **BLOCKED** with zero
executed rows for all three target journeys (J-05, J-06, J-07) and a budget-deferred J-04. The
reviewer's `definition_of_done: complete` and QA's PASS both overstate the evidence position.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap): TC-5's "zero non-200s, zero connection failures" is measurably breached in both live drills; the DoD's "TC-1 through TC-9 all pass" line is false**

`docs/phases/goal-ops-hardening-iter-51.md:243-246` requires that every 1/s `GET /api/health` poll
across the finalize tail answers HTTP 200 with "zero non-200s, zero connection failures". Both live
drills contradict it:

- Solo drill (`reports/perf-budgets.md`, Addendum 11, "New finding"): **9 of 653 polls** returned
  curl `code=000` (connection-level non-answer, each hitting the 5.0s `--max-time` ceiling), all 9
  inside the new `factor_lab_all_warm` window (22:24:54Z–22:29:47Z against the phase's
  22:20:57Z–22:30:40Z span), none anywhere else.
- Concurrent drill (`reports/phase-goal-ops-hardening-iter-51-ui-test-results.llm.md`, UT-08):
  **19 of 892 polls (2.13%)** non-200, clustered around `forward_aggregates_warm horizon=20`'s
  573.87s span — the run's longest sub-phase, *not* the new one (which measured 0.05s that run).

The mechanism is the spec's own GIL-contention diagnosis: any sufficiently long tight CPU-bound
finalize-tail sub-phase running in-process can starve the accept loop past a full connection cycle.
This iteration does not create that class (iter-50 already measured it on the request path) but it
does add a new ~584s in-process window per ingest in which it can fire. Both artifacts disclose it
honestly and neither hides it behind a green headline — the defect is that the DoD checkbox and the
review's `definition_of_done: complete` were nonetheless recorded as satisfied.

**Not fixed here, deliberately.** The spec's own OUT OF SCOPE (`:173-174`) excludes closing J-07
step 2, and the only known fix shapes (move the compute off-process, or chunk the loops with explicit
yield points) are excluded at `:168-170`. Applying either now would also breach TC-8 — see §4.

**B2 — IMPORTANT (gap): TC-6's cache-HIT requirement did not hold live — a mid-ingest Factor Lab request still triggers the full live compute**

TC-6 (`:247-251`) requires a concurrent mid-warm `/research/factor-lab?all=true` to complete "without
triggering a live `compute_factor_lab_all`". UT-08 ran exactly that drill and the opposite happened:
the browser request arrived ~35–50s into job id=325, i.e. **before** the finalize tail reached its
own `factor_lab_all_warm` phase (which sits 8th, after `forward_aggregates_warm`'s 1003.37s), so the
*request* became the single-flight owner, rendered the labelled `slow-compute-notice` counter for
tens of minutes, and the tail's own phase then logged **0.05s** as a no-op
(`...-ui-test-results.llm.md`, UT-08 phase breakdown).

What the drill *does* prove is the wedge-class hazard is contained: one compute, not N (single-flight
worked as designed), zero `MemoryError`/`Traceback`/500 anywhere, both pages resolved with fresh
correct data, no permanent hang. So the honest scope of the fix is narrower than the GOAL sentence
"never computing live on the request path": it is **"never on the request path after an ingest job's
finalize tail has completed"**. TC-2's own wording ("given TC-1's ingest has just completed") is
scoped that way; TC-6's is not, and TC-6 is the one that failed.

**B3 — GAP: the phase's honesty gate is a degrade gate, not the "persisted this run" gate its own comment and the dev handoff claim it mirrors**

`apps/backend/app/engine/data_manager.py:4283-4284` states the gate mirrors "`index_series_warm`'s
'persisted this run' honesty gate just above"; the dev handoff repeats it. It does not.
`index_series_warm` (`:4246-4248`) appends only when `index_series_cached_with_status` reports a row
was persisted *this run*; the new gate (`:4291-4300`) appends whenever the returned payload carries
no degrade signal. Two consequences:

1. On a genuine cache HIT nothing was refreshed this run, yet `"factor_lab_all"` is still appended
   (asserted deliberately by `test_finalize_hook_factor_lab_all_second_run_still_reported_on_cache_hit`).
   This is defensible — it matches `research_hot_keys_warm`'s convention, and a HIT can only be a row
   at the *current* stamp — but two categories in the same `aggregates_refreshed` list now carry
   different semantics, and the code comment describes the wrong one.
2. `factor_lab_all_cached` swallows a failed cache write (`apps/backend/app/engine/research.py:3975-3979`:
   `try: session.commit() / except Exception: session.rollback()` then `return payload`). On that path
   a clean, non-degraded payload is returned with **no persisted row**, the phase appends
   `"factor_lab_all"`, `/data` displays "factor lab all" under "Refreshed:", and the next Factor Lab
   view pays the full 578–875s compute. Low likelihood (the comment's stated cause is a racing writer
   that already wrote the identical row), but it is the one path where the category can be claimed
   untruthfully. A one-line existence re-check before the append would close it; I did not apply it
   (see §4).

**B4 — GAP: only the default all-history key is warmed — `as_of`-scoped all-factors views, and any post-ingest dataset-version bump, still route to a live request-path compute**

`factor_lab_all_cached` keys on `(subject, view, asof_key, dataset_version+token, horizon)`
(`research.py:3818-3831`), and `GET /api/research/factor-lab?all=true&as_of=D` resolves a cutoff and
passes it straight through (`apps/backend/app/api/research.py:126`). The warm calls `as_of=None` only
— deliberate per the spec ("never a per-as-of sweep", `:4269-4270` comment). So the "As of date" mode
the UI exposes (exercised in UT-07) is still a potential multi-minute request-path compute, and any
dataset-version bump between ingest and page view (`_dataset_version` = `max(scanner_runs.id)` +
`count(forward_returns)`, `research.py:2346-2361`) re-opens the cold path. Scoped, disclosed, and not
this iteration's deliverable — recorded so the GOAL sentence's "ever/always" is not read wider than
the evidence supports.

**B5 — GAP: the ~584s phase stamps one heartbeat before the call, so `/data`'s live job card reads "possibly stalled" for the phase's whole duration**

The spec asks for a "`prog.tick()` heartbeat before/during the call since this phase can run several
minutes" (`:105-106`). Only "before" is implemented (`data_manager.py:4289`); `compute_factor_lab_all`
exposes no progress hook. `last_progress_at` therefore freezes for ~584s while
`config.yaml:87` sets `heartbeat_stale_seconds: 20.0`, and `apps/frontend/app/data/page.tsx:2527,2545`
renders "· possibly stalled" past that threshold on a running job. Pre-existing in kind — the UT-08
run shows `forward_aggregates_warm horizon=20` going 573.87s between ticks — and J-09's replay row
still passed, so this is an additional misleading window per ingest rather than a new failure class.

### Frontend Findings

None. No frontend file is in the diff (`git diff --stat`), and the spec's Frontend section is "None".
The one frontend-visible surface — `/data`'s "Refreshed:" line — was verified byte-identical against
`GET /api/data` run id=323 in UT-03.

### Test Findings

**T1 — GAP: the per-`(factor,horizon)` half of the honesty gate has no test, and the browser test that would have covered it end-to-end was skipped**

The gate has two branches (`data_manager.py:4291-4298`): whole-response `factors_status ==
"unavailable"`, and any `by_horizon[].status == "unavailable"`. Only the first is tested
(`test_finalize_hook_factor_lab_all_never_reported_on_whole_response_degrade`). The second is the
branch the real per-entry isolation path produces (`research.py:1324`, `:1339`) and is exactly what
UT-05 would have exercised in-process via the real injection site
`data_manager._fault_inject_memory_error("factor_lab_all")` (`research.py:1297`) — UT-05 was SKIPPED
on a permission denial, so J-07 step 4's induced-abort case carries no evidence this round. I
exercised the gate expression against all three payload shapes myself; the untested branch is
logically correct (clean → `False`; whole-response degrade → `True`; per-entry degrade → `True`), so
this is a coverage gap, not a live defect.

**T2 — OBSERVATION: TC-4 part 2 is a negative assertion with no in-test positive control**

`test_combination_cohort_members_strict_no_full_range_allocation` asserts a monkeypatched
`research_module.set` never sees `range(pool_n)`. A broken interception would pass vacuously. I
verified independently that patching `research_module.set` *does* intercept `research.py`'s own calls
(observed one intercepted `set(...)` call — the new `set(single_members[0])` copy — during a 5,000-row
run), so the assertion is meaningful today. Asserting the interceptor fires at least once would make
the test self-proving.

**T3 — OBSERVATION: test quality is otherwise tight.** The 9 new tests assert exact values (cache-row
identity, `asof_key == "all"`, `horizon == default_horizon`, exactly one row after two runs,
`_release_process_memory()` called, the category's presence/absence per branch), and the pinned
pre-fix oracle is a verbatim copy rather than a call into the current function. Independently re-run:
`.venv/bin/python -m pytest tests/test_data_manager.py tests/test_research_streaming.py -k "factor_lab_all or combination_cohort_members or finalize_hook" -q -p no:randomly`
→ **50 passed in 257.39s**.

### Verification / Process Findings

**V1 — IMPORTANT (gap): the DoD's journey lines are unmet and the review + QA verdicts overstate completion**

- `reports/phase-goal-ops-hardening-iter-51-ui-test-results.md` records **"Browser QA Verdict:
  BLOCKED"**, with "no test case executed by any lane" for **all three target journeys** (`UT-J-05`,
  `UT-J-06`, `UT-J-07`) and `UT-J-04` (a required-still-passing journey) marked `DEFERRED-BUDGET`
  under SPEED-15 trim rung 2. The deterministic replay covered only J-01/J-03/J-08/J-09 (4/4 PASS).
  This is the exact pattern that file's own "Missing Target Journeys" preamble cites from iter-41/42.
- `reports/qa/goal-ops-hardening-iter-51-qa.md` returned PASS with "Browser Checks: SKIPPED", no
  functional test plan executed, and the claim "implementation matches spec" — it ran before the
  browser lane and evaluated none of TC-2/3/5/6/8.
- `reports/reviews/goal-ops-hardening-iter-51-review.md` recorded `spec_alignment.definition_of_done:
  complete` at a point when TC-3, TC-5 and TC-6 had not been executed, and demoted the disclosed
  health-poll breach to `severity: NOTE`.
- `reports/phase-goal-ops-hardening-iter-51-ux-regression.md` is `UX-REGRESSION-SKIPPED` (trim rung 3b).

TC-8's *sequencing* rule does hold: latest product-code mtimes are `data_manager.py` 2026-08-06
10:24:46 and `research.py` 2026-08-06 08:29:28, both far earlier than the lane's results file
(2026-08-07 01:56:01). The lane simply was not the full 8-journey lane TC-8 describes.

### Verified clean (checked directly, no finding)

- **AG-10:** `git diff --stat` over `config.yaml`, `project-extensions/host-guard/host-guard.env`,
  `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` — **empty**.
- **AG-7:** no key/secret/token/password-shaped string anywhere in the `apps/` + `perf-budgets.md` diff.
- **AG-9:** both drills are seed/offline backfills (`"source": null` on the persisted job record).
- **AG-5:** no scoring/return semantics touched; the `_combination_cohort_members` change is
  allocation-strategy only, byte-identical by construction (the full range is the identity element
  under `&`) and proven so against the pinned oracle.
- **Zero-conditions branch:** the new `else: strict_members = set()` differs from the old full-pool
  behavior but is unreachable — `app/config.py:1105` boot-validates `1 <= min_conditions`, and both
  callers (`research.py:1635`, `samples.py:252`) gate on it. The reviewer's NOTE stands as an accurate
  comment-wording nit, not a defect.

---

## 3. Domain Assessment

The core domain logic is sound and the change is genuinely surgical.

**The warm phase.** It calls the *same* function the request path calls
(`factor_lab_all_cached(session, cfg, as_of=None)` vs `api/research.py:126`'s
`factor_lab_all_cached(session, cfg, as_of=cutoff)` with `cutoff=None` when `as_of` is omitted), so
there is one producer and no second derivation — the count-coherence/single-source discipline this
codebase enforces elsewhere is preserved. Placement is safe with respect to cache-key validity:
`_dataset_version` depends on `max(scanner_runs.id)` and `count(forward_returns)`, both fixed by the
time `_do_backfill` returns, and nothing after the finalize tail writes either — so the row written
at position 8 is still current when the job flips to `ok`. My live-DB check confirms that empirically
(row stamp == current stamp, and exactly one row: the stale-prune works, no cache growth).

**Isolation and honesty.** `except MemoryError` precedes `except Exception`, `_release_process_memory()`
runs on the memory path, the phase-timing line is logged unconditionally in the non-`finally` position
its siblings use, and the degrade gate reads the *real* fields `factor_lab_all_cached` itself uses to
decide not to persist — the developer checked the producer rather than assuming, which is the right
instinct and is what makes the "the call didn't raise ≠ a row was written" reasoning correct. The one
uncovered write-failure path is B3.

**The allocation bound.** Correct and correctly justified. The copy in `set(single_members[0])` is
load-bearing (`&=` mutates in place and `single_members` is returned to every caller); omitting it
would have corrupted the first single-condition cohort, and the byte-identical test would have caught
it. Honest sizing: at the live pool of ~1.25M observations this removes roughly one ~1.25M-entry set
while `_composite_scores`' per-condition rank lists of the same order remain — a real reduction, not
an elimination of the neighborhood's memory pressure, which is what the spec claimed (a diagnostic
bound on "the exact frame logged before the wedge", not a claimed wedge fix).

**Where the product actually stands.** The user-visible outcome the iteration exists for is real and
measured through the real UI: Factor Lab opens on stored rows in milliseconds after an ingest, sort/
expand/mode controls work on the cached payload, and the `/data` "Refreshed:" line honestly names the
new category byte-identically to the API. What is *not* closed, and is now better characterised than
before, is J-07: the health-poll breach is not specific to this phase's code — UT-08 shows it
attaching to whichever finalize-tail sub-phase happens to be longest — which is a more useful
diagnosis than the iteration set out to produce.

---

## 4. Fixes Applied During This Audit

**None.** No source file was modified.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fix applied |

Rationale, stated explicitly because it is a judgment call:

- B1 and B2 are the carried J-07 residual. Both fix shapes are named in this iteration's own OUT OF
  SCOPE (`:168-170`, `:173-174`) and one of them ("move `compute_factor_lab_all` off-process") is the
  logged road-not-taken in `assumptions.md`. Applying either would be scope creep on a risky path.
- B3, B4, B5, T1 and T2 are GAP/OBSERVATION class. Fixing them is scope creep per the audit rules.
- Decisively: TC-8 (`:257-261`) makes any product-code change after the lane ran trigger a **mandatory
  full 8-journey re-run before scoring**. The lane already ran last (mtimes verified above). Editing
  `apps/backend/app/**` now to close a non-critical finding would invalidate the only completed lane
  evidence this iteration has and leave the sequencing rule breached for a 6th consecutive round —
  strictly worse than carrying the findings forward.

---

## 5. Recommended Next Step

Do **not** treat this iteration as closing J-05/J-06/J-07; treat it as closing the Factor Lab's
request-path compute (which it demonstrably does) and as producing a sharper J-07 diagnosis.

The next iteration should spend its one risky change on the finding both drills now converge on:
**connection-level `/api/health` starvation is a property of any long tight CPU-bound finalize-tail
sub-phase**, not of `factor_lab_all_warm` specifically (solo drill: inside the new phase; concurrent
drill: inside `forward_aggregates_warm h20`). That points at a scheduling fix — moving the finalize
tail's heavy loops off the event-loop-adjacent thread pool, or chunking them with explicit yield
points — over any further memory-side change, and it needs an owner decision because the off-process
option is currently OUT OF SCOPE by the spec's own text.

Ahead of that, three cheap items are worth folding into the next decomposition rather than being
scheduled as their own work:

1. **Close the verification debt first, before new code** — J-05/J-06/J-07 have zero executed rows
   and J-04 is two rounds stale. A lane-only round would give the evaluator its first real reading on
   the target journeys since the fix landed.
2. **B3's one-line honesty tightening** — re-check the row exists at the current stamp before
   appending `"factor_lab_all"`, so a swallowed cache-write failure can never be reported as a
   refresh, plus a test for the untested per-entry degrade branch (T1).
3. **Re-run TC-5 with an isolated poller** — Addendum 11's own methodological caveat (the poller
   shared the host) is the one thing that could still explain part of the `code=000` cluster, and it
   is cheap to eliminate before spending an iteration on a scheduling change.
