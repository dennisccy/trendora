# goal-ops-hardening-iter-38 Audit Report

**Date:** 2026-07-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration did the hard thing it was dispatched to do: the throwaway drill's shared bar cache was
genuinely live this time (`dates_total: 3` in both arms' job status, and the new liveness line proven in the
LIVE `logs/backend.log:142444` / `:143130` / `:143652`, not in a saved excerpt), and J-07 step 1 really was
re-run through a backfill's ingest-finalize hook on the full deep basis instead of `GET /api/backtest`
(`evidence_generated_at` moved 2026-07-30T03:04:33Z → 12:22:41Z for all 5 horizons — a genuine cold
recompute). But the headline two-arm number it published was **wrong**: the fallback arm's "finalize-tail-only
Δ 238.5 MB" was anchored on a sample taken 31.8 s into that job (mid backfill-compute stage) and labelled
"end-of-backfill-stage". Recomputed from the raw CSVs, the fallback arm's tail delta is **0.0 MB** against the
live arm's 229.0 MB — the qualitative conclusion in `perf-budgets.md` was reversed. I corrected the record in
place (B1, CRITICAL, fixed, with a re-runnable recompute script) and corrected an overstated
"full-duration" health-poll claim (B2). What remains: J-07 step 4 has **no this-iteration evidence** in the
shipped configuration, and the deterministic replay lane is 1/7 green with J-04 unverified live.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): the two-arm finalize-tail VmPeak comparison — this iteration's single headline
measurement — was mis-anchored, and its published conclusion was the opposite of what the data shows**

`reports/perf-budgets.md:4831` (as published) and
`runs/goal-ops-hardening-iter-38/mem-drill/two-arm-summary.json` reported
`VmPeak at end-of-backfill-stage → tail-only peak … 3,320,896 KB → 3,565,104 KB (tail-only Δ 238.5 MB)` for
the forced-fallback arm, and drew the conclusion "close between the two arms … within ~4% … the iter-37
auditor's 'a resident cache could raise peak' hypothesis is **not corroborated**". The dev handoff repeated the
claim that the tail-only delta "is computed from the end-of-backfill-stage reading forward, which WAS captured
for both arms."

That anchor is not an end-of-backfill-stage reading. The fallback monitor
(`mem-drill/arm-fallback-monitor-final.csv`) starts **31.8 s after** the fallback job was submitted
(job `started_at` 12:10:57.34Z; CSV window reconstructed from its own mtime as 12:11:29.15Z–12:15:28.65Z),
i.e. mid backfill-compute stage — the JSON's own note even says the first sample "already reflects the
backfill-compute stage's own … prefill", which is exactly why it cannot also be the stage's end. The published
238.5 MB therefore silently included the remaining ~40 s of that arm's **compute** stage, while the live arm's
3,370,480 KB anchor was a genuine end-of-stage reading — the two numbers were not measuring the same interval.

Recomputed (`runs/goal-ops-hardening-iter-38/mem-drill/audit-recompute-tail-deltas.py` → `.out`; the same
script reproduces the live arm's published 3,370,480 KB anchor **exactly**, which validates the method):

| | live-cache arm | forced-fallback arm |
|---|---|---|
| VmPeak at end-of-backfill-stage | 3,370,480 KB | **3,565,104 KB** (already its overall peak) |
| VmPeak overall | 3,604,964 KB | 3,565,104 KB |
| **finalize-tail-only Δ** | **+229.0 MB** | **+0.0 MB** (published as 238.5 MB) |

Anchor-free corroboration, needing no timestamp arithmetic: the fallback arm's VmPeak is **flat** from monitor
t=62.631 s through job completion (~263 s), and its VmRSS collapses 3,101,404 → 1,564,872 KB right at that
point — the pre-iter-37 stage-exit cache release. Its tail adds nothing under **any** anchor at or after that
sample.

Corrected reading: holding the shared cache resident across the tail **does** raise tail-stage VmPeak
(+229.0 MB vs +0.0 MB) — the iter-37 auditor's hypothesis is directionally *corroborated* for the tail, not
refuted — while the **overall** peak difference is small (live 38.9 MB / 1.1% higher) because the fallback arm
front-loads the same growth into its compute stage instead. The wall-clock finding (fallback 2.61x slower) is
unaffected. Both arms stay far under the 4608 MB drill cap, so nothing about the shipped behavior is unsafe —
but the *answer to the question this iteration existed to answer* was published backwards.

**Fix applied.** `reports/perf-budgets.md:4831-4849` (corrected row + an `AUDIT CORRECTION` block + rewritten
"Reading the result honestly" paragraph), `perf-budgets.md:4942` (TC-2 row), `mem-drill/two-arm-summary.json`
(corrected `finalize_tail_only_delta_mb`, original value retained as
`finalize_tail_only_delta_mb_as_first_published`), and an appended correction section in the dev handoff.
**Verification:** `python3 runs/goal-ops-hardening-iter-38/mem-drill/audit-recompute-tail-deltas.py`
(output committed as `audit-recompute-tail-deltas.out`) — reproduces the live arm's anchor exactly, prints the
corrected fallback anchor/delta, and re-derives the anchor-free flatness check; JSON re-parsed clean
(`json.load` OK). No source file was touched by this fix.

**B2 — IMPORTANT (fixed at the disclosure level; the coverage gap itself stands): the live-basis 1 Hz health
poll did not cover the full duration of the warm it claims to cover**

`perf-budgets.md`'s TC-4 bullet was titled "1Hz health poll, **full duration**" and reported "Max gap between
consecutive poll starts … **2.355 s**". Reconstructed from the artifacts' own timestamps: the job ran
12:20:42.67Z → 12:26:20.68Z (338 s); `j07-warm/monitor.out` (233 polls, its own `MAX_SECONDS=300` cap) was
written at 12:25:49.82Z and `monitor-part2.out`'s single poll at 12:26:26.69Z — already after the job reached
`ok`. That leaves a **~37 s window with no health poll, ~31 s of it while the finalize tail was still
running**. The true max inter-poll gap in this evidence is ~37 s, not 2.355 s, and J-07 step 2's "no frozen or
unresponsive window" is established over ~88% of the warm (through the forward-aggregate horizons, which
completed 12:22:41Z), not over all of it. Nothing suggests the backend *was* unresponsive there — it simply
was not sampled; the honest status of that stretch is `unknown`.

**Fix applied.** `perf-budgets.md:4917-4938` (bullet retitled, `AUDIT CORRECTION` block added) and
`perf-budgets.md:4944` (TC-4 row downgraded **PASS → PARTIAL**); dev handoff annotated.
**Verification:** recomputed from `j07-warm/health-latency.csv` directly — 233 polls, max in-segment gap
2.355 s, 0 non-200, latency min/max/mean 0.1087 / 1.3172 / 0.2829 s (233/233 above the ≤0.1 s owner-item
budget, consistent with iter-34/j) — plus the mtime/`started_at`/`finished_at` reconstruction above.

**B3 — GAP: the `read_pool()` wall-clock figure (TC-10) is prose-only and partly arithmetic, not the
in-situ measurement TC-10 asked for**

`perf-budgets.md`'s "0.5628 ms per call" micro-benchmark has no committed script, no raw output, and no
re-run command anywhere in `runs/goal-ops-hardening-iter-38/`; the "~20,680 calls" it is projected against is
exactly `1,880 × 11`, i.e. derived from the batch width (`config.yaml:921
membership_timeline_batch_symbols: 50`, 548-symbol pool → 11 batches), not an instrumented count. TC-10 asked
for "a wall-clock measurement … taken on the live basis **during a representative multi-date backfill**"; what
was delivered is a standalone micro-benchmark plus a projection. Rubric §5 ("Data/metric is X" → needs the
computing artifact, never prose) puts the figure at `unknown`. Not fixed (re-measuring is new work, not a
surgical correction); annotated in place at `perf-budgets.md:4951` so the number is not read as harder
evidence than it is.

**B4 — IMPORTANT (not fixed — needs a live drill): J-07 step 4 has no this-iteration evidence in the shipped
configuration; the one trial that did induce pressure produced a crash-class abort, not the per-item isolation
step 4 asserts**

J-07 step 4 (goal.md:277-280) is: *induce memory pressure during a warm; assert the warm aborts honestly per
the existing isolation convention while the SAME process keeps serving `/api/health` and previously cached
reads*. The spec's TESTING REQUIREMENTS name the mechanism precisely — "a `MemoryError` raised mid-warm under a
tightened `server.memory_cap_mb` … must be caught by the existing per-item handler"
(`data_manager.py:3401-3407` / `:3435-3440`). What this iteration actually ran:

- The **canonical** drill was deliberately re-calibrated **away** from pressure: `config.scratch.yaml:1363`
  raises the cap 3072 → 4608 MB with the stated reason "widened so BOTH arms complete gracefully". Both arms
  finished `ok`; no `MemoryError`, no abort, no isolation path exercised. The "induced-pressure drill" induced
  no pressure.
- The **3072 MB** trial did hit a ceiling, but in the *fallback* arm and in the wrong place: job
  `43bd7dd7…` failed inside `_do_backfill`'s initial prefill with `RuntimeError: can't start new thread`
  (`mem-drill/arm-fallback-3072cap-crash-monitor.out`, final status `failed`, `dates_done: 0`,
  `aggregates_refreshed: []`, VmPeak pinned at exactly 3,145,728 KB). That is a `ulimit -v` thread-spawn
  failure during the compute stage — not a `MemoryError` mid-warm caught by the per-item handler. The job did
  fail *honestly* and the process kept answering `GET /api/data/jobs/{id}` (the monitor read the `failed`
  status over HTTP), which is real but partial: **no `/api/health` poll and no cached-read check accompanied
  that trial**, so the two things step 4 actually asserts were not sampled.
- The 970 MB attempt killed the boot warm-up daemon before any job was submitted (disclosed in
  `perf-budgets.md`).

Consequence: DEFINITION OF DONE item 1 — "all four steps carry THIS-iteration evidence" — is **not met** for
step 4. Steps 1-3 are met (with B2's coverage caveat on step 2). Not fixable inside an audit: closing it
requires another live throwaway drill via `scripts/start-backend.sh` at a cap tight enough to trigger the
per-item `MemoryError` path, with a concurrent `/api/health` poll and a previously-cached read — bounded work,
but new measurement, and AG-10 makes ad-hoc heavy compute on this host the wrong thing for an auditor to
improvise.

**B5 — OBSERVATION: the TEST-ONLY env toggle is truthiness-gated, so `TRENDORA_FORCE_LEGACY_BAR_CACHE=0`
*enables* legacy mode**

`data_manager.py:3123` — `if not os.environ.get("TRENDORA_FORCE_LEGACY_BAR_CACHE")`. Any non-empty value,
including `"0"` / `"false"`, skips the stash. The placement itself is right (one choke point, downstream
consumers fall back through their existing `is not None` checks — verified at `:3351` and
`_persist_per_date_coverage_snapshots`), and the variable is genuinely absent from the running backend's
environment (checked `/proc/855233/environ`) and from every script in the repo (only docs/handoff references).
Low risk; worth a `in ("1","true","yes")` guard if it survives past this iteration.

**B6 — OBSERVATION: "fresh-boot baseline" (live arm) is a sample 5.8 s into the job**

`perf-budgets.md:4830` labels the live arm's 1,833,040 KB as the fresh-boot baseline; the recompute shows that
monitor started 5.8 s after job submission. Same class as B1 but harmless — the derived Δ 1,730.4 MB is a
slight *under*statement, and no conclusion rests on it. Left as-is.

### Frontend Findings

None — `Frontend Present: no`, zero frontend files in the diff, `ui-surface-map` confirms no user-visible
surface change. Correctly scoped.

### Test Findings

**T1 — IMPORTANT (not fixed): the regression evidence for the seven required-still-passing journeys does not
meet TC-11, and the QA report's "no regressions" claim cites the wrong artifact**

TC-11 requires "zero FAIL rows and zero reconciliation overturns". Actual
(`reports/phase-goal-ops-hardening-iter-38-regression-replay-results.md`): the deterministic lane returned
**1/7 PASS** (J-06 only) with six FAIL rows, all of them selector/locator timeouts characteristic of stale
golden scripts rather than product breakage. Four (J-01, J-03, J-08, J-09) were then overturned by the LLM
lane; the reconciliation footer omits J-04 and J-05, which also had FAIL rows — J-05 was in fact overturned to
PASS and J-04 became SKIPPED, so the footer under-reports its own overturns. Net truthful position from the
merged file: J-01, J-03, J-05, J-06, J-08, J-09 re-confirmed live with detailed evidence; **J-04 not verified
this iteration** (browser-QA declined to restart the backend under an explicit pipeline instruction, and said
so honestly). Nothing in this backend-only diff plausibly regresses J-04 (boot path untouched; the developer
and the drills booted the backend cleanly ~6 times, ~1 s to healthy each), so I read this as unverified rather
than broken — but the deterministic safety net is effectively down, which is what rubric §2's "deterministic
gates green" exists to catch.

Separately, `reports/qa/goal-ops-hardening-iter-38-qa.md:260` records "No regressions (J-01 … J-09) ✓ PASS |
Shared-cache coverage tests passing". Unit tests are not journey-regression evidence (rubric §5 ✖ pattern
verbatim). QA ran before the browser lane and could not have cited the replay — the defect is asserting PASS
on a criterion it had no evidence for, rather than writing `unknown`.

**T2 — verified good: TC-6 and TC-7 are load-bearing, not vacuous** (spot-verified, since these are the
iteration's only new safety net). `test_data_manager.py:2168` faults `_checkpoint_run_record` *conditionally on
`prog._shared_bar_cache is not None`*, so the fault can only fire after the real stash — the post-fault
`is None` assertion would fail if `data_manager.py:3183`'s reset line were deleted. `test_data_manager.py:2264`
monkeypatches the module-global `_refresh_ingest_aggregates`, which is exactly how `run_data_job` calls it
(`data_manager.py:4313`), so the forced-fallback arm is genuinely exercised. Both pass per the reviewer's own
live run and QA's `157 passed in 614.45s` (`qa.md:57`) — accepted with citation, not re-run.

**T3 — OBSERVATION: no test covers the new env toggle or the liveness log line.** Both are drill-support code;
a two-line test (`monkeypatch.setenv` → assert `prog._shared_bar_cache is None` after `_do_backfill`) would
pin the escape hatch's behavior so it cannot silently rot into a real code path. Not required by the spec.

---

## 3. Domain Assessment

The domain logic this iteration touched is sound and, importantly, *small*. The env toggle sits at the single
choke point (`data_manager.py:3123`) and produces the pre-iter-37 behavior by omission — no parallel code path,
which is the right shape for a measurement harness. The liveness line (`:3361-3365`) is placed after
`cache_ctx` resolves and before the `with`, reports the branch actually taken, and — critically — I found all
11 of its emissions in the live `logs/backend.log`, including `nullcontext` lines for the zero-work backfills
browser-QA triggered later (correct: `_do_backfill` returns before the stash when `targets` is empty). The
`.warning`-instead-of-`.info` workaround is ugly but honest and disclosed; the root-logger gap is the real bug
and is correctly deferred.

The docstring fix (TC-8) is genuinely a fix, not a no-op edit: the old text described a whole-pool
`prefilled_bar_cache` scan, while `_excluded_counts_by_date` now either reuses an active outer cache or walks
the pool in 50-symbol batches replacing one `_BarCache`'s contents. The new text matches the code I read. The
548 vs 591 correction (TC-9) is right for the figure it annotates — the batch-width bound scales with
`read_pool()`'s candidate pool, not `symbol_count`.

On the substance of J-07 itself: the corrected measurement (B1) is *more* interesting than the one originally
published, and it is not bad news. Holding the ~1.13 GB cache across the tail costs ~229 MB of tail-stage
growth and ~1.1% of overall peak, and buys 2.6x wall-clock — at 58.6% of the declared 6144 MB cap on the live
basis there is ample headroom either way. The shipped behavior is fine; only the write-up was wrong.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `reports/perf-budgets.md` (:4831, :4833-4849, :4942) | Corrected the fallback arm's mis-anchored tail-only delta (238.5 MB → 0.0 MB), added an `AUDIT CORRECTION` block, rewrote the "Reading the result honestly" paragraph so the conclusion matches the data (tail-stage penalty corroborated; overall peak +1.1%), updated the TC-2 row |
| 2 | Critical | `runs/goal-ops-hardening-iter-38/mem-drill/two-arm-summary.json` | Same correction in the raw summary; original figure retained as `finalize_tail_only_delta_mb_as_first_published`; mislabelled anchor note rewritten |
| 3 | Critical | `runs/goal-ops-hardening-iter-38/mem-drill/audit-recompute-tail-deltas.py` + `.out` (new) | Re-runnable recomputation from the raw CSVs — validates itself by reproducing the live arm's published anchor exactly, plus an anchor-free flatness check |
| 4 | Important | `reports/perf-budgets.md` (:4917-4938, :4944) | Disclosed the ~37 s unpolled window in the live-basis health poll; TC-4 row downgraded PASS → PARTIAL |
| 5 | Gap | `reports/perf-budgets.md` (:4951) | Annotated the `read_pool()` figure as prose-only/derived, not an in-situ measurement |
| 6 | — | `docs/handoffs/goal-ops-hardening-iter-38-dev.md` | Appended an "Audit corrections" section superseding the two invalidated claims |

No source file was modified by this audit (`git diff --stat` shows `data_manager.py` / `test_data_manager.py`
carrying the developer's changes only), so no test re-run was required; each fix is verified by the
recomputation output cited above.

---

## 5. Recommended Next Step

Do **not** re-open the shipped shared-cache code — it is measured, bounded, and correct. Two things are owed:

1. **Close J-07 step 4 for real (small, bounded).** One throwaway-DB drill via `scripts/start-backend.sh` at a
   cap tight enough to raise a `MemoryError` *inside the aggregate warm* (not at the prefill), with a
   concurrent 1 Hz `/api/health` poll and one previously-cached read (`GET /api/backtest?as_of=<warm date>`)
   asserted 200 during and after the abort. That is the one assertion J-07 step 4 makes and the only step
   without this-iteration evidence. While there, run the health poll to job termination (B2) — a
   `MAX_SECONDS` bound that expires before the job does is what created the ~37 s hole.
2. **Repair the deterministic replay lane (T1).** 6/7 golden scripts fail on locator timeouts; the lane is
   currently supplying no regression signal, and every iteration is paying for an LLM re-run to overturn it.
   J-04 in particular has now gone an iteration without live verification.

Given B1's correction, the evaluator should read J-07 as **materially advanced but not yet four-for-four**:
steps 1-3 carry genuine, independently-verifiable this-iteration evidence (live-log liveness lines, real K=3
target, all 5 horizons recomputed through the ingest-finalize hook, VmPeak 58.6% of cap); step 2 is verified
over ~88% of the warm; step 4 is not verified this iteration. `partial` with a one-drill path to `passing` is
the honest status, not `passing`.
