# goal-ops-hardening-iter-29 Audit Report

**Date:** 2026-07-28
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The iteration's *stated* fix shipped but did not bind: the join accumulator was chunked by
`read_batch_size` = 2000 used as a **run count**, against a live basis of only 1,812–1,871 distinct runs
per horizon — so the loop produced exactly one chunk and peak accumulator size was **0.0% below the pre-fix
figure at every horizon** (measured directly on `apps/backend/data/trendora.db`). I fixed that during this
audit (own config key, 14.4× lower peak, proven by test + live measurement). What I could not fix, and what
forces the FAIL, is B2: `/research/factor-lab` — a nav page two clicks from the dashboard — returns HTTP 500
from a live `MemoryError` on **every** visit (4/4 requests in `logs/backend.log`, QA reproduced 3×), which
fails this spec's own DoD item TC-9 and is a live AG-8 violation. It is pre-existing and outside the diff,
but its root cause (the output pools, not just the accumulator) needs a redesign, not a surgical patch.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): the delivered memory bound was inert on the live basis — 0% peak reduction**

`apps/backend/app/engine/research.py` (line 264 as shipped, 275 after this audit's edit) shipped as
`for start in range(0, len(runs_with_fr), batch)` with `batch = config.research.read_batch_size` = 2000.
`read_batch_size` counts **rows** (it is the `yield_per` size, per its own config docstring); it was reused
verbatim as a **run-id** chunk width. Measured against the live DB (read-only,
`file:apps/backend/data/trendora.db?mode=ro`):

| horizon | distinct runs | chunks produced | total pairs | peak chunk | reduction |
|---|---|---|---|---|---|
| 1 | 1871 | **1** | 803,042 | 803,042 | **0.0%** |
| 5 | 1867 | **1** | 800,826 | 800,826 | **0.0%** |
| 10 | 1862 | **1** | 798,051 | 798,051 | **0.0%** |
| 20 | 1852 | **1** | 792,507 | 792,507 | **0.0%** |
| 60 | 1812 | **1** | 770,299 | 770,299 | **0.0%** |

Every horizon degenerated to a single chunk, so `_fr_slice_map` rebuilt the *entire* pre-fix accumulator —
including the exact 803,042-pair figure the spec's BACKGROUND cites as the AG-8 defect. The ceiling the fix
installed (2000 runs × ~429 symbols/run ≈ **858,000** pairs) sits *above* the pre-fix measured peak. The
phase GOAL ("bound … so it can never exhaust the backend's memory") was therefore not achieved on today's
data; only future growth past 2,000 runs would have been capped. This is not theoretical: this box produced
live `MemoryError`s in this very module during this iteration's own QA window (see B2).

**Fix applied.** The chunk width is now its own config key, `research.factor_join_run_chunk` (a RUN count,
default `100`), leaving `read_batch_size` its documented ROW meaning:
- `apps/backend/app/config.py:1336` — new defaulted field on `ResearchCfg`; boot validation at 1360-1361.
- `config.yaml:890` — `factor_join_run_chunk: 100` with the measurement in the comment.
- `apps/backend/app/engine/research.py:239-244, 275-276` — reads the new key for the loop stride/slice bound;
  `batch` still drives `yield_per`. No literal added (research.py is a `CALC_FILES` no-magic-numbers file).

Evidence the fix binds, same read-only method, h=20: **19 chunks, 55,195-entry peak (14.4× lower)**, with
identical row sets (792,507 FR rows / 769,894 SR rows at every width) and **no latency cost** — SQL wall time
0.72 s at width 100 vs 1.01 s at width 2000 (the scoped index seeks beat the single covering-index scan).

**B2 — CRITICAL (gap — NOT fixed, requires its own iteration): `/research/factor-lab` returns 500 on every
visit from a live `MemoryError`**

`apps/backend/app/engine/research.py:463-532` (`_all_factor_observations_by_horizon`). `FactorLabPage`
unconditionally requests `?all=true` on mount → `factor_lab_all_cached` → `compute_factor_lab_all` →
`_all_factor_observations_by_horizon`, which builds `fr_by_h` (traceback line 497) as one map across **every** horizon
and run in a single pass, then `pools` (traceback line 508) as ~770K observation dicts **per horizon**. Confirmed
independently of the QA report: `logs/backend.log` contains **4** `GET /api/research/factor-lab?all=true`
requests and **all 4 returned 500**, with tracebacks terminating at `research.py:497` and `research.py:508` (the same two statements sit at 508
and 519 in the current file — this audit's edits shifted the module by 11 lines).
The process survives (uvicorn logs `Exception in ASGI application`), but the page shows the generic "Backend
unavailable" fallback.

This fails the spec's DoD item "The Factor Lab secondary consumer is unaffected (TC-9)" and its acceptance
clause ("decile table and rank-IC figures render with real numeric values — no console error, no blank or
empty table"). It is also a live AG-8 violation ("widening the data basis must never crash an existing page
or exhaust a service's memory") on a page reachable in two ordinary sidebar clicks.

**Attribution (verified, not assumed):** `git diff` shows this function is untouched by iter-29 — the defect
is pre-existing, and iter-29's mandated regression check is what surfaced it. There is no evidence it ever
succeeded on the current basis: those 4 requests are the only Factor-Lab-all requests in 9 days of log.

**Not fixed, deliberately.** Only *one* of the two crash sites (`fr_by_h`) is amenable to B1's
chunking template. The other (`pools`) is the function's **return shape** — ~770K dicts × 5
horizons — which no accumulator bound touches; removing it requires streaming the decile aggregation or
precomputing the all-view, i.e. a design change. Patching only the accumulator would move the crash, not remove it,
and would violate the spec's own rule against bundling a second risky change. Recommended as the next
iteration's scope (the ux-regression reviewer reached the same conclusion independently).

**B3 — OBSERVATION: the broad `except Exception` in `build_evidence_payload` will also mask genuine bugs**

`apps/backend/app/engine/evidence.py:169-183`. The spec asked for exactly this ("`MemoryError` or
otherwise"), it logs via `logger.exception`, and the failure is disclosed in the UI — so this is by design,
not a defect. Worth recording only because a future `TypeError` from a refactor will now surface to users as
a calm "Unavailable — monitored and refreshed as new data arrives." rather than a loud failure. The
`except MemoryError` clause above it is redundant (a subclass of `Exception`) but is not harmful — it
produces a distinct log line.

**B4 — GAP (pre-existing, out of scope): `test_no_magic_numbers.py` is red on this branch**

`tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` fails on float literals in
`indicators.py` (`0.5`, `0.95`) and `forward_testing.py` (`45.0`, `0.5`, `0.9`). Neither file is modified in
the working tree, so this predates iter-29 and is unrelated to it — but it means the architecture principle
it enforces is currently unguarded. `research.py` is clean (my fix added a config key, not a literal). No
agent in this iteration ran this selector.

### Frontend Findings

No findings. `resolveDrawdownExpectationsPanelState` (`apps/frontend/lib/evidence.ts:310-318`) is a pure,
correctly-ordered three-way resolver: `expectations` truthy wins first, then `expectations_status`, then
absent — so the pre-existing honest-None path is genuinely byte-unchanged, and the new state cannot mask it.
`DrawdownExpectationsPanel` (`apps/frontend/app/evidence/page.tsx:254-278`) branches on it and nothing else.
The API route (`apps/backend/app/api/evidence.py:27`) returns a bare `dict` with no response model, so the
new key is not stripped in transit — the disclosure is genuinely reachable end-to-end, which QA's UT-05
confirmed against the real page (exactly 1 note, verbatim copy, other 6 cards untouched) and UT-06 confirmed
stylistically (identical computed style to the sibling "Pending" note, zero icons).

### Test Findings

**T1 — IMPORTANT (fixed): TC-1 proves the chunking *mechanism*, never the shipped *property***

`apps/backend/tests/test_research_streaming.py` drove all three iter-29 proofs through `_cfg_batch(2)` — an
artificial 2-run chunk width. Those tests pass identically whether the shipped configuration chunks anything
or nothing, which is exactly how B1 shipped green. Two tests added, both at the **real** `load_config()`:
- `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` — pins the shipped width `<= 500`
  against the measured 1,812–1,871 runs/horizon. **RED/GREEN proven:** temporarily setting the yaml value
  back to the shipped `2000` fails it (`assert 2000 <= 500`); at `100` it passes.
- `test_factor_observations_chunks_at_the_shipped_config` — builds a `width + 3`-run fixture and asserts
  `_factor_observations` made ≥ 2 slice reads with no slice holding the whole fixture, catching any future
  re-coupling of the run width to the row batch.

`_cfg_batch(batch, run_chunk=None)` now defaults `run_chunk` to `batch`, so every pre-existing chunk-
independence probe keeps varying both knobs exactly as before the split.

**T2 — IMPORTANT (gap): QA recorded TC-09 as PASS against a page that had rendered nothing**

`reports/qa/goal-ops-hardening-iter-29-qa.md:157-172` reports TC-09 PASS on the evidence "Decile table text
found ('decile' in DOM)". The string "decile" is in the page's *static intro copy* ("expandable in place to
its full decile grid"), so the assertion is satisfied by a page that fetched nothing. QA's own saved
screenshot, `reports/qa/goal-ops-hardening-iter-29-evidence/TC-09-factor-lab-loaded.png`, shows the page in
**skeleton/loading state** — grey placeholder bars, no table, no rank-IC — while the backend was returning
500. The DoD item was signed off on a substring match against a blank page. Not fixed (a QA-process finding,
not a code defect); recorded so the same substring check is not reused as a rendering proof.

**T3 — IMPORTANT (gap): the two TARGET journeys J-06 and J-07 were never exercised this iteration**

The browser-qa dispatch's own note is explicit
(`reports/phase-goal-ops-hardening-iter-29-ui-test-results.llm.md:176`): *"No golden script written for
UT-07/J-06/J-07 … this iteration's actual target journeys J-06/J-07 were not in this dispatch's
regression-journey list."* Consequences against the DoD:
- **TC-10 not run.** `runs/goal-session-ops-hardening/journey-scripts/J-06.json` exists but is absent from
  `reports/phase-goal-ops-hardening-iter-29-regression-replay-results.md` (which covers J-01/03/04/05/08/09
  only). This was iter-28's explicitly carried gap ("fixed at iter-28, never exercised through the
  deterministic replay lane since") and it is still carried.
- **TC-8 not run.** `reports/perf-budgets.md` is unmodified (`git status` clean) and contains no iter-29
  entry, so no `/evidence` reading was recorded against its committed budget and no 11-page sweep happened.
- TC-6's substance *is* covered by UT-01/UT-02 (7/7 cards, 0.24–0.89 s, zero MemoryError/ASGI lines in the
  window) and TC-7's substance by UT-J-05 (`aggregates_refreshed` includes `drawdown_expectations`) plus
  UT-J-03's 283-date backfill — but neither J-06 nor J-07 has a journey-level verdict from this iteration.

---

## 3. Domain Assessment

The domain logic that *was* written is correct, and I verified it by reading rather than trusting.

The chunked rewrite's byte-identity argument holds: `runs_with_fr` is sorted, slices are non-overlapping
contiguous ranges, and each slice's `ScannerResult` scan re-applies the same `ORDER BY run_id, id`, so
concatenation reproduces the original global order. The join can never miss, because a slice's accumulator
and its `ScannerResult` filter use the identical `run_id.in_(slice_run_ids)` set. Duplicate-key ambiguity —
the one way per-slice `last-write-wins` could diverge from global `last-write-wins` — is impossible:
`forward_returns` carries `UNIQUE (run_id, symbol, horizon)` (`models.py:388`). No-lookahead is preserved
because the `as_of` filter moved to the `runs_with_fr` discovery query, which is upstream of every derived
structure. TC-2's pinned pre-fix oracle is a real regression oracle (it re-implements the old body and calls
the same unchanged helpers), and TC-3's assertion is tight (every returned `run_id`'s `ScannerRun.asof_date`
must be `<= D`).

TC-4 is likewise a genuine isolation proof, not a smoke test: two independently resolvable claims, a
monkeypatch that raises for exactly one, and assertions on *both* rows including the surviving row's actual
figures (`horizon == 20`, `exp_phase["n"] == 1`). The added `assert "expectations_status" not in
payload["claims"][0]` on the pre-existing unresolvable-claim test is the right guard: it pins that the new
field is additive on the exception path only.

The one substantive domain gap is scope, and the spec acknowledged it: bounding the accumulator was always
only half the memory footprint of this path — `observations` itself still materializes ~770K dicts, which
the plan explicitly declined to touch ("downstream `_deciles` need it whole"). That is defensible for
`/evidence` (cache-served, 0.24–0.89 s warm), but it is precisely why B2's sibling cannot be fixed by
chunking alone. Note also that TC-7's premise — that the `data_manager.py` `MemoryError` catch is "no longer
needed once `_factor_observations` is bounded" — was never true at the shipped width and remains unproven at
the audited width; the defense-in-depth catch was correctly left in place either way.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/config.py` | New `ResearchCfg.factor_join_run_chunk: int = 100` (RUN-count accumulator width, distinct unit from the ROW-count `read_batch_size`) + boot validation `>= 1` |
| 2 | Critical | `config.yaml` | `research.factor_join_run_chunk: 100`, with the live measurement recorded in the comment |
| 3 | Critical | `apps/backend/app/engine/research.py` | `_factor_observations` reads the new key for its chunk stride/slice bound (`batch` still drives `yield_per` only); docstring corrected to state the two knobs are different units |
| 4 | Important | `apps/backend/tests/test_research_streaming.py` | `_cfg_batch(batch, run_chunk=None)` (defaults to `batch`, so existing probes are unchanged); + `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`; + `test_factor_observations_chunks_at_the_shipped_config` (both at the real `load_config()`) |
| 5 | — | `docs/handoffs/goal-ops-hardening-iter-29-dev.md` | Appended "Audit correction" superseding the two Fix-1 claims the measurements contradicted |

**Verification of these fixes (commands and results):**

- Targeted: `pytest tests/test_research_streaming.py -v -k "shipped or chunk_bounded or unchunked_reference
  or as_of_excludes"` → **6 passed in 1.04s** (TC-1, TC-2 ×2, TC-3, and both new audit tests).
- RED proof: with `config.yaml` temporarily reverted to `factor_join_run_chunk: 2000`, the new guard fails —
  `AssertionError: research.factor_join_run_chunk=2000 cannot bound the join accumulator on the live basis
  (1,812-1,871 distinct runs/horizon): it must be <= 500` — then restored to `100` and re-verified green.
- Regression sweep (one combined invocation, `taskset -c 0-3,8-11`, BLAS/OMP capped per
  `project-extensions/host-guard/host-guard.env`): `test_research_streaming.py test_evidence.py
  test_research.py test_factor_lab_all.py test_regime_phase_factor.py test_iter20_research_cluster.py
  test_phase_severity_lab.py test_regime_lab.py test_samples.py test_severity_velocity.py test_config.py
  test_config_engine.py` → **435 passed in 51.65s**, zero failures (superset of the dev's and reviewer's own
  312-test sweep, plus both config suites, which prove the real `config.yaml` still boot-validates).
- Live effect, read-only SQL against `apps/backend/data/trendora.db` at h=20: width 2000 → 1 chunk /
  792,507-entry peak / 1.01 s; width 100 → 19 chunks / 55,195-entry peak / 0.72 s; identical row counts
  (792,507 FR, 769,894 SR) at every width.
- Diff re-read (`git diff apps/backend/app/config.py config.yaml apps/backend/app/engine/research.py`): three
  functional lines in `research.py`, one defaulted field + one validator line in `config.py`, one yaml value.
  No unrelated change; nothing else in the iteration's diff touched.
- `test_no_magic_numbers.py` was run and its failure confirmed pre-existing (offenders are in `indicators.py`
  / `forward_testing.py`, both unmodified in the working tree; `research.py` is not among them).

The new config value takes effect at the next backend start; the currently running process still holds the
boot-time config.

---

## 5. Recommended Next Step

**Do not treat iter-29 as closed, and do not consider GOAL_ACHIEVED.** The spec's own closing note said the
next decomposer should check whether closing AG-8 makes this the GOAL_ACHIEVED point — it does not:

1. **Next iteration's scope should be B2:** `_all_factor_observations_by_horizon`. It needs both the
   accumulator bound (B1's `_fr_slice_map` template applies directly to `fr_by_h`) **and** a way to stop
   materializing ~770K observation dicts per horizon — stream the decile aggregation, or serve the all-view
   from a precomputed/ingest-warmed cache the way `/evidence` already serves its expectations. Patching only
   `fr_by_h` will move the crash from the accumulator to the pools loop, not remove it.
2. **Re-run the target journeys.** J-06 and J-07 have no verdict from this iteration; TC-8 and TC-10 in
   particular are unexercised, and TC-10 is now a two-iteration carry. J-06's 11-page sweep must also record
   its `/evidence` reading in `reports/perf-budgets.md`.
3. **Re-measure B1's fix on the live basis after the next backend restart** — the unit tests and the SQL-level
   measurement are solid, but no live `/api/evidence` or Factor-Lab request has yet run under
   `factor_join_run_chunk: 100`.
4. **Non-blocking carries:** `test_no_magic_numbers.py` is red on unrelated files (B4); the QA lane should
   stop accepting substring-in-DOM as a rendering proof (T2); `_combination_observations` /
   `_event_study_members` remain named, deferred siblings; and `/data`'s `outcome:"failed"` with an empty
   `reason` (observed in UT-J-09) is worth a line of its own somewhere.
