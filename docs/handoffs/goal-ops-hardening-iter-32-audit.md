# goal-ops-hardening-iter-32 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal was genuinely achieved, and it survives the two lessons this spec was built around
(iter-30 "bound the frame in the traceback, not its neighbours" and iter-31 "a constant-factor win
wearing a bound's clothes"). I did not take the handoff's or the oracle's word for it: I re-derived
byte-identity independently (the shipped oracle had stopped covering one of its ten keys), and I
measured the bound at the real live scale — recomputing horizon 20 for `as_of=2026-07-21` (771,129
observations) with the new code produced a payload whose SHA-256 is **identical** to the payload the
OLD code cached for that same key at 05:05Z today, while peak RSS fell from **981 MB → 170 MB** at
unchanged runtime (10.8s → 10.7s). Two verification defects were found and fixed during this audit: the
TC-1 test measured a quantity dominated by the spec's *excluded* term (it fails on correct shipped code
at any realistic n), and the TC-2 oracle compared the `attribution` key against itself — a deliberate
attribution defect passed 47/47 before the fix and fails 39 assertions after it. Remaining gaps are
non-blocking and documented.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, not fixed): `_ExactMeanAcc.add()` raises on non-finite input where
`statistics.mean()` degraded gracefully**

`apps/backend/app/engine/forward_testing.py:626` calls `value.as_integer_ratio()` directly, which raises
`ValueError` on NaN and `OverflowError` on ±Inf. CPython's `statistics._sum` special-cases those
(`partials[None]`) and returns a NaN/Inf mean instead. So a non-finite stored return would now raise
where it previously produced a NaN cell — on `GET /api/backtest` that is a 500 instead of a `NaN` in the
payload (arguably better, but it is a behavior change).

The reviewer flagged this as low-risk by inference; I measured the reachability instead of asserting it:

- Producer gate: `forward_return()` returns `None` when `entry_close is None or == 0`
  (`forward_testing.py:169-174`), so no 0/0.
- Live data (read-only query over `apps/backend/data/trendora.db`, 3,971,375 rows):
  `realized_return` — 0 NULL, 0 non-`real` typeof, 0 values beyond ±1e307, range
  `[-0.9496026927959414, 5.230844793713163]`; `max_drawdown` — 0 non-`real` typeof.

Unreachable on the current basis and on any basis the current producer can generate. Left as-is (a
guard would be scope creep and would itself change behavior); recorded so a future ingest source that
can emit non-finite floats reopens it.

**B2 — OBSERVATION: `_group_means` / `_group_mdd` now have ZERO production call sites, and both the
docstring and the handoff claim otherwise**

After this iteration, every production consumer routes through `_group_means_from_accs`
(`forward_testing.py:1328/1337/1342/1354-1356`) or `_AttributionAccumulator` — `_group_means`
(`forward_testing.py:713`) and `_group_mdd` (`:699`) are reachable only from
`test_forward_testing_aggregates_streaming.py`'s reference oracle. The docstring at
`forward_testing.py:1172-1174` and the dev handoff both state they are still "used by
`compute_run_scorecard`'s own already-small per-run `stock_obs`"; that is no longer true —
`compute_run_scorecard` reaches attribution through `_AttributionAccumulator.from_observations`
(`:2126-2128`) and otherwise only calls `_control_groups`.

Keep both functions: they are what makes TC-2 an independent oracle (see T2). The risk is a future
"dead code" sweep deleting the oracle's reference implementation on the strength of that inaccurate
comment. Comment-only correction — not fixed here (scope creep).

**B3 — OBSERVATION: one wrong timestamp in the `reports/perf-budgets.md` iter-32 section**

`reports/perf-budgets.md:4032-4033` records the boot banner as `2026-07-29T08:20Z`; the log line it
cites (`logs/backend.log:133067-133070`) reads `=== start-backend.sh: launching at 2026-07-29T07:20:50Z
===` / `Started server process [719044]`. One hour off, and inconsistent with the section's own trial
timestamps (07:22:57Z / 07:25:10Z, both UTC). Every other number in that section checks out against the
log and the DB (see §3). Cosmetic; not fixed.

### Test Findings

**T1 — IMPORTANT (fixed): the shipped TC-1 test measured an aggregate dominated by the spec's
*excluded* term, so it proved the bound only at the small `n` it was calibrated at**

The spec's TC-1 asks for "a tracemalloc-measured peak size **attributable to the by-group/per-stock
accumulation paths**", explicitly exempting the disclosed bare-float `distribution` list. The shipped
test (`test_forward_testing_aggregates_streaming.py:675`) measured the whole accumulation including that
exempt list, and asserted `peak_large < peak_small * 4.0` at 40 → 200 observations. Measured on the
**correct shipped code** with the test's own harness:

| n (5x delta) | shipped ratio | shipped 4.0x threshold |
|---|---|---|
| 40 → 200 | 2.00x | pass |
| 5,000 → 25,000 | 4.70x | **fail** |
| 20,000 → 100,000 | 4.77x | **fail** |

i.e. the metric converges on fully-proportional growth as the surviving linear term stops being diluted
by fixed overhead — the assertion is satisfiable only at small `n`, and would raise a false alarm on
correct code if anyone raised it. (It did discriminate against the reverted design at its chosen `n`:
5.61x vs 2.00x, so it was not vacuous — but it did not measure what it claimed.) I rated this IMPORTANT
rather than GAP because DoD item 1 cites this test as its verification; I was genuinely between the two
levels.

The quantity TC-1 actually names IS bounded — measured with the exempt list excluded:
**1.62x (40→200), 1.29x (5,000→25,000), 1.09x (20,000→100,000)**, i.e. 25.5 kB → 27.8 kB while
observations grow 5x (the residual is `_ExactMeanAcc`'s distinct-denominator partials, bounded by the
exponent range of IEEE-754 doubles).

**Fix applied** (`test_forward_testing_aggregates_streaming.py:646-660, 700-730`): added
`retain_distribution=False` to the synthetic-accumulation helper and a second, isolated, scale-robust
assertion at 5,000 → 25,000 with a 2.0x threshold. Evidence:

- `pytest tests/test_forward_testing_aggregates_streaming.py::test_accumulator_peak_size_does_not_scale_with_observation_count_at_fixed_cardinality -q` → **1 passed in 0.81s**
- Revert-simulation with the identical harness (full `stock_obs` dict list, 5,000 → 25,000):
  `2,474,376 → 12,411,560 bytes, ratio 5.02x` → **fails** the new assertion. The new assertion catches
  the exact regression it exists for, at a scale where the old one no longer could.

**T2 — IMPORTANT (fixed): TC-2's byte-identity oracle compared the `attribution` key against itself —
demonstrated blind to a real attribution defect**

`_reference_compute_forward_aggregates` is the "pinned pre-rewrite reference" the whole file exists for.
The developer updated its attribution call site to
`_attribution_slices(_AttributionAccumulator.from_observations(stock_obs, ...), cfg)` — so for
`attribution` (1 of the 10 top-level keys TC-2 enumerates) both sides of the comparison executed the
**new** implementation. The old `_per_stock_attribution` body was deleted from the module, so nothing in
the repo pinned the previous behavior.

Demonstrated, not theorised — mutation test (swap `contributors`/`detractors` inside
`_AttributionAccumulator.per_stock`, a defect that inverts J-19's headline panel):

- with the developer's oracle wiring: **47 passed** (defect undetected)
- with the audit's restored reference: **39 failed, 8 passed** (defect caught)

**Fix applied** (`test_forward_testing_aggregates_streaming.py:66-110, 225`): added
`_reference_per_stock_attribution` / `_reference_attribution_slices` — the verbatim pre-iter-32 bodies
from `git show HEAD:apps/backend/app/engine/forward_testing.py` — and pointed the reference at them.
`_group_means` / `_distribution` / `_rank_band_label` stay imported from the module because this
iteration left them byte-unchanged. Evidence: `pytest tests/test_forward_testing_aggregates_streaming.py -q`
→ **47 passed in 7.67s**; full dev/QA set re-run → **143 passed, 7 deselected in 16.21s**.

**T3 — OBSERVATION: two QA rows assert more than the evidence they cite**

- QA TC-01 states the pass criterion as "growth ratio < 1.5x when observation count **doubles**" and
  marks it PASS from a test that uses a 5x delta and a 4.0x threshold. The stated criterion was never
  the one evaluated (see T1).
- QA TC-09 marks the six-journey replay PASS while its Actual column says "deterministic replay
  verification **deferred** to goal-evaluator". The replay did in fact run and pass in this iteration —
  `reports/phase-goal-ops-hardening-iter-32-regression-replay-results.md`, 6/6 journeys, zero FAIL rows,
  screenshots under `reports/qa/goal-ops-hardening-iter-32-evidence/` — so the verdict is right but the
  citation in the QA report is not. Conclusion unaffected.

**T4 — OBSERVATION: the spec's "nine `_attribution_slices` direct-call unit tests" premise was factually
wrong; the developer handled it correctly**

Only three of the nine named tests call `_attribution_slices` directly
(`test_forward_testing.py:1194/1217/1234`); the other six call `compute_forward_aggregates` and needed
no change. All nine pass, none deleted, none weakened — verified against the diff: the signature-pinning
test still asserts a structural signature (`{"acc", "cfg"}`), the empty-observations and
single-observation NA behaviors are asserted unchanged. The dev handoff disclosed the discrepancy; QA's
report repeats the spec's incorrect "all nine direct-call" framing. No product impact.

---

## 3. Domain Assessment

**The bound is real, and it is the frame the traceback named.** `stock_obs.append` is gone; every
consumer is fed inside the existing per-chunk loop (`forward_testing.py:1268-1286`). What remains
per-observation is (a) the spec's disclosed bare-float `distribution` list and (b) `chunk_obs_by_run`,
bounded to `forward_agg_run_chunk` (=100 runs) × symbols-per-run — the same bound iter-30 established.
Live measurement, one horizon, 771,129 observations, identical process/env for both arms
(`ulimit -v 6291456`, `taskset -c 0-3,8-11`, BLAS/OMP/NUMEXPR=4):

| arm | maxrss | duration | overall.n |
|---|---|---|---|
| OLD (`git show HEAD:...forward_testing.py`) | **981 MB** | 10.8 s | 771,129 |
| NEW (working tree) | **170 MB** | 10.7 s | 771,129 |

~918 MB → ~108 MB above a 62 MB baseline, at unchanged runtime — the exact-`Fraction` streaming mean
costs nothing measurable. This answers the iter-31 challenge ("which term did it remove?"): the
per-observation *dict* term is gone; only the disclosed float-list term survives, one order of magnitude
smaller.

**Byte-identity holds at live scale, not just on fixtures.** The DB gave me a natural pre/post
experiment: `forward_aggregate_cache` rows for `asof_key='2026-07-21'` were written by the OLD code at
05:04–05:05Z, before this iteration's edit (`forward_testing.py` mtime 06:35Z; iteration started 06:13Z),
under the same `dataset_version=r1879-f3971375`. Recomputing that key with the new code yields a payload
whose `json.dumps(..., sort_keys=True)` SHA-256 equals the cached one exactly
(`dcf155dff4aed66f…`), including `attribution`, `control_group` and `overall`. AG-3 (displayed numbers
correct) and AG-5 (determinism) hold at production scale.

**Independent differential verification** (randomized, adversarial; `_ExactMeanAcc` vs `statistics.mean`
over 400 shuffled-order trials including denormals, ±1e308, ±0.0; `_group_means` vs
`_group_means_from_accs` over 40 trials × 5 group specs with `None` groups, missing drawdowns, padding
and out-of-order extras; OLD vs NEW `_attribution_slices` over 40 trials plus 30 `compute_run_scorecard`-
shaped trials whose observations carry no `max_drawdown`/`regime` key at all; `_control_groups` vs
`_ControlGroupBuilder` driven chunk-by-chunk over 30 trials including >3 chunk widths at the shipped
`forward_agg_run_chunk=100`): **0 mismatches**, compared structurally with type checks and sign-of-zero
sensitivity, not `approx`.

**TC-6's RNG-order argument is sound by construction, not by luck.** `_forward_agg_runs_with_fr` returns
`sorted(...)` (`forward_testing.py:1087`); chunks are consecutive ascending slices of it; `consume_run`
is called in `sorted(chunk_obs_by_run)` order within each chunk — so the global draw order is the same
ascending run-id sequence `_control_groups` walks, with one shared `random.Random`. `bm_returns` for a
chunk's runs is populated before that chunk's `consume_run` loop, so sector-ETF lookups resolve exactly
as with the full map.

**TC-4/TC-5 evidence is real, not a no-op warm.** Independently re-derived: `grep -c MemoryError` from
`logs/backend.log:133070` forward = **0**; 279 `GET /api/health` lines after the banner, **zero non-200**;
zero ERROR/Traceback lines. The warms genuinely computed — `forward_aggregate_cache` gained 10 rows in
exactly the two claimed windows (07:23:07–07:23:55 and 07:25:21–07:26:09), 5 horizons each, with
`overall.n` = 780,337 / 779,253 / 776,543 / 771,129 / 749,441 and `attribution.distribution.n ==
overall.n` in every one. The `VmPeak` figure (2,691,600 kB, 57.2% margin) is a process ceiling that the
warm never moved — the report says so explicitly rather than implying the warm caused it, which is the
honest framing.

**Anti-goals.** AG-3/AG-5 verified above; AG-7 no credentials in the diff; AG-8 materially advanced (the
named finding is closed, the other three carried findings untouched); AG-9 no network path added (the
warm read only the committed local seed); AG-10 launch scripts and `project-extensions/host-guard/`
untouched by this diff (`git diff` empty for `host-guard.env`), and every command in this audit ran under
the same `taskset -c 0-3,8-11` + 4-thread caps. AG-1/AG-2/AG-4/AG-6 are not in this iteration's
territory (no new claim, score, or ledger entry).

**DEFINITION OF DONE status** (full trace where risk or my own leads warranted it; reviewer+QA citation
where the item is mechanical):

| # | Item | Status |
|---|---|---|
| 1 | Per-group/per-run consumers no longer scale with observation count (TC-1) | **Met** — traced in full; measured 1.09x at 20k→100k, live 981→170 MB. Its shipped test was weak (T1, fixed) |
| 2 | Byte-identical to the reference oracle (TC-2) | **Met** — traced in full; live-scale SHA-256 identity + 0 differential mismatches. Oracle coverage hole (T2) fixed |
| 3 | Nine `_attribution_slices` tests updated, none weakened (TC-3) | **Met** — traced against the diff; see T4 on the spec's premise. Reviewer PASS + QA TC-03 row (9/9) |
| 4 | Live warm: zero `MemoryError`, health stays 200 (TC-4) | **Met** — re-derived from `logs/backend.log` + cache rows |
| 5 | `VmPeak` + margin in `reports/perf-budgets.md` (TC-5) | **Met** — section present; one wrong timestamp (B3) |
| 6 | `_control_groups` RNG output unchanged (TC-6) | **Met** — 30-trial chunked differential + live-scale identity |
| 7 | `compute_run_scorecard`'s own `stock_obs` byte-unchanged (TC-7) | **Met in substance** — builder byte-unchanged by diff; one call-site line changed, mechanically forced by the spec's own authorized signature lift, disclosed by the developer, and proven output-identical (30 scorecard-shaped differential trials + 20/20 `test_backtest_scorecard.py`) |
| 8 | Evaluator re-derives the four AG-8 findings (TC-8) | **Downstream** — evaluator lane; TC-1 and TC-4 both hold, so iter-29/c is eligible to close |
| 9 | Six journeys replay green (TC-9) | **Met** — 6/6 with screenshots in the replay report (QA's citation was wrong, T3) |
| — | J-07 evaluated against its four acceptance steps | **Met** at API/process level per the plan's stated iter-30/31 precedent |
| — | No anti-goal violation; tests pass; handoff written | **Met** — 143 passed / 7 deselected re-run post-fix |

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_forward_testing_aggregates_streaming.py` (`:646-660`, `:700-730`) | TC-1: added `retain_distribution=False` to the synthetic-accumulation helper and a second assertion isolating the by-group/per-stock paths at 5,000→25,000 (`<2.0x`; shipped 1.29x, reverted design 5.02x). The original assertion is untouched. |
| 2 | Important | `apps/backend/tests/test_forward_testing_aggregates_streaming.py` (`:36`, `:66-110`, `:225`) | TC-2: restored the oracle's independence for the `attribution` key by pinning the verbatim pre-iter-32 `_per_stock_attribution` / `_attribution_slices` bodies as `_reference_*` helpers instead of calling the new implementation. |

No production code was modified by this audit; `git status` shows only the three files the developer
already touched. Post-fix verification: `pytest tests/test_forward_testing_aggregates_streaming.py -q` →
47 passed; the full dev/QA command (streaming + scorecard + forward_testing with the same 7 deselects) →
**143 passed, 7 deselected in 16.21s**; mutation probe confirms fix 2 is load-bearing (39 failed with it,
47 passed without it).

The dev handoff's claim that the TC-1 unit test "is the isolated, mechanism-level proof of the actual
bound" is true only after fix 1; its claim that the reference oracle "stays the obviously correct
full-list implementation" for attribution is true only after fix 2. Both are noted here rather than
edited into the handoff, which stands as the developer's own record.

---

## 5. Recommended Next Step

Proceed to the evaluator / next iteration. The `stock_obs` AG-8 finding (iter-29/c) is closed on
evidence I re-derived independently: bounded accumulators, byte-identical output at live scale, and a
981 MB → 170 MB peak reduction on the real basis. Carry forward, unchanged:

1. The three still-open AG-8 findings (`warmup.py:194`, `prices.py:141`, Factor-Lab-all's constant-factor
   residual) — none touched this iteration, as specified.
2. J-06's `scripts/start-frontend.sh` dev-vs-prod launcher decision + real-browser TTI sweep — the spec's
   named next scope.
3. B2 (correct the docstring/handoff claim that `_group_means`/`_group_mdd` still have production
   callers, and mark them explicitly as the test oracle's pinned reference so no future cleanup deletes
   them) and B3 (the one wrong boot-banner timestamp in `reports/perf-budgets.md`) — both one-line
   documentation items, suitable for a lean iteration, neither blocking.
4. The `merge_ui_test_results.py` `_ROW_RE` framework bug remains a pre-achievement blocker for the
   human/framework maintainer — a third consecutive iteration flagging it.
