# goal-ops-hardening-iter-36 Audit Report

**Date:** 2026-07-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration actually shipped what iter-35 planned: `_membership_timeline`'s candidate-pool bar
loading is genuinely bounded (I independently reproduced the 70.7% peak reduction), the
`/api/evidence` `stored_by_key` read is chunked with an honestly-disclosed modest (~4%) benefit, and
all four sibling research labs are wired to the same `resolveLabLoadPanel` states as Regime Lab. Two
IMPORTANT findings: the spec's TC-2 byte-identity oracle covered only the membership-timeline half
and left the higher-risk change (`_compute_coverage_uncached` dropping its outer bar-cache wrap)
unproven — **fixed during this audit** with a live-basis test whose liveness I negative-controlled;
and DoD item 1, "J-07 passes via browser-qa-agent", was **never executed** — the browser-QA lane
carries no J-07 row and skipped both `/data` and `/evidence` regression tests, which I partially
closed by hand against a real backend. Nothing found is a correctness defect in shipped code.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): TC-2's byte-identity oracle omits the coverage payload, leaving this
iteration's higher-risk `data_manager` change unproven**

`apps/backend/tests/test_membership_timeline_batch_bound.py:197`
(`test_membership_timeline_byte_identical_to_pinned_reference_on_live_seed`) compares only
`_membership_timeline`'s own dict — `candidate_pool_count` / `points` / `labels`. The phase spec's
TC-2 and DoD item 5 name the *served coverage payload* (`universe_count`, `per_symbol`,
`membership_timeline`, `gaps`, `capacity`).

That omission is not cosmetic. This iteration made **two** `data_manager` edits, and the second one —
`_compute_coverage_uncached` (`apps/backend/app/engine/data_manager.py:865`) no longer opening its own
`prefilled_bar_cache` around `_compute_coverage_body` — is the one with real byte-identity exposure,
because it flips which branch two coverage readers take on the standalone entry point
(`refresh_coverage_snapshot`'s ingest-finalize call, the boot warm-up safety net, a cold tooling call):

- `_resolved_universe` → `universe_resolver.resolve_with_reasons`
  (`apps/backend/app/engine/universe_resolver.py:174-185`) — was the `active_bar_cache` branch
  (`trailing_count` over the once-loaded series + cached `bars_asof` returning `Bar` records); is now
  the no-cache branch (grouped `count(DailyPrice.id) WHERE date <= asof` + per-symbol `DailyPrice` ORM
  `bars_asof`). Feeds `universe_count`, `universe_asof`, `candidate_pool_count`,
  `universe_diagnostic`, `absent_from_latest_snapshot`.
- `_trading_days` (`apps/backend/app/engine/data_manager.py:153-160`) → `bars_asof(benchmark, latest)`
  — same branch flip. Feeds `trading_day_count`, `gap_count`, `gap_first`/`gap_last`, `gaps_preview`
  and the intra-series-gap diagnostic's calendar.

Neither was covered by any live-basis proof. The reviewer flagged the same omission
(`reports/reviews/goal-ops-hardening-iter-36-review.md`, MINOR issue at line 197) and the dev handoff
asserts equivalence in prose only ("Byte-identical figures either way", `data_manager.py:863`). A
prose claim is not evidence.

**Fix applied** — added
`test_coverage_payload_bar_readers_byte_identical_with_and_without_outer_cache` to
`apps/backend/tests/test_membership_timeline_batch_bound.py`. It pins exactly the two cache-sensitive
readers on the live seed DB, comparing the pre-fix (bar-cache-active) and shipped (no-cache) branches.
Bounded by construction — the cached side is built one shipped-width batch at a time via
`_BarCache.load_only`, never `prefill`, so the module does not add a second whole-table load. That is
a sound proof of the full-pool claim because `resolve_with_reasons` classifies each candidate
independently (per-symbol trailing count → per-symbol gates → a per-reason tally with no cross-symbol
interaction), so branch-agreement on every symbol of a batch is branch-agreement on any union of
batches. Every other coverage field (`per_symbol`, the missing-data diagnostic, the snapshot/price
aggregates) is grouped SQL that never consults the bar cache and therefore cannot differ.

Verification (§4 has the commands): 16 resolver comparisons across 4 real 50-symbol batches × 4 real
as-of dates + the 5,383-date benchmark calendar — **0 divergences**, 1 passed in 44.86 s; then
**4 passed** for the whole module. Liveness negative-controlled (see T2) so this is not a vacuous
oracle.

**B2 — IMPORTANT (gap, partially closed): DoD item 1 — "J-07 passes via browser-qa-agent" — was
never executed**

`reports/phase-goal-ops-hardening-iter-36-ui-test-results.md` contains **no J-07 row at all** (the
`UT-J-*` rows are the six required-still-passing regression journeys). The two P1 tests that would
have verified this iteration's backend fixes at the user-visible surface are both SKIPPED:

- `UT-13` (`/data` coverage panel unchanged) and `UT-14` (`/evidence` expectations panel renders real
  figures) — reason recorded at
  `reports/phase-goal-ops-hardening-iter-36-ui-test-results.llm.md:239-249`: the browser-QA agent
  stopped the backend for the error-state tests and "was blocked by the permission system from
  restarting it … three attempts denied".

`runs/goal-ops-hardening-iter-36/status.json:26` records `"browser_checks_run": false`. None of TC-4's
named content ran: no full-horizon forward-aggregate warm, no 1 Hz `/api/health` poll, no VmPeak
margin comparison, no re-verification of the induced-memory-pressure drill against the bounded paths
in a live lane. The QA report nonetheless reports "**TC-4 (regression):** Backend health 200,
readiness ready, no obvious memory regression vs iter-34 baseline — PASS"
(`reports/qa/goal-ops-hardening-iter-36-qa.md:113`), which rests on a single health ping — an
overstated PASS against the evidence floor for "no regressions".

**Partially closed during this audit.** I booted the real backend via `scripts/start-backend.sh`
(AG-10 host-guard block applied; `ulimit -v` 6,291,456 KB from `server.memory_cap_mb=6144`) and
executed UT-13's and UT-14's substance plus the health-poll and VmPeak-margin halves of TC-4:

| Check | Result |
|---|---|
| `/api/health`, 30 polls at 1 Hz | 30/30 HTTP 200, max latency **132 ms**, `readiness: ready` |
| VmPeak vs cap (PID 3405500) | **2,691,796 KB / 6,291,456 KB = 42.8 %**; margin 3,599,660 KB |
| `/api/data` (UT-13) | `universe_count` 540, `universe_asof` 2026-07-22, `candidate_pool_count` 548, `symbol_count` 591, `snapshot_count` 1880, `trading_day_count` 5383, `coverage_status: current`, `membership_timeline` 1,880 points. Internally consistent: 548 − (2+1+4+1 excluded) = 540 |
| `/api/evidence` (UT-14) | 7 claims, **all** with real `expectations` panels — no `expectations_status: "unavailable"`. e.g. claim 1 / Expansion: n=41,801, `max_drawdown` median −0.07485, p90 −0.03616, `insufficient: false` on all five phases |

**Residual, explicitly unverified:** J-07's full-horizon forward-aggregate warm and its induced
memory-pressure drill were not re-run in a browser-QA lane. They are covered only by the dev's own
unit-level drill (TC-8, which I did re-run — see §4) and the dev's self-reported live run. J-07's
journey status from this iteration's own evidence is honestly **unknown**, not `passing`.

**B3 — GAP: ledger finding iter-29/d is only partially closed — a sibling whole-table prefill remains
on the same ingest-finalize warm chain**

`_persist_per_date_coverage_snapshots` (`apps/backend/app/engine/data_manager.py:3183`) still opens
`with prefilled_bar_cache(session, expected_symbols=pool_symbols)` around a multi-date backfill's
per-date coverage warm, and `_do_backfill` (`data_manager.py:3085`) does the same for the scan. So a
multi-date backfill still materializes the whole `daily_prices` table (the 1.13 GB this iteration
measured), and J-07's Acceptance clause — "no unbounded whole-table ORM materialization remains on the
warm OR SERVING path" — is not yet fully met. This is *within* the spec's IN SCOPE boundary (which
named only `_membership_timeline`'s and `_compute_coverage_uncached`'s own loading), and the dev
disclosed it honestly in the handoff Known Issues and `reports/perf-budgets.md:4532-4545`.

Confirmed first-hand: `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`
(`apps/backend/tests/test_bar_cache.py:424`) still fails — max per-symbol load count **10**, typical
**2** (`assert 10 == 1`). The reviewer independently confirmed via `git stash` that unmodified HEAD
gives 11/3, i.e. a net improvement, not a regression. The common single-latest-date daily ingest is
genuinely bounded now (`_persist_per_date_coverage_snapshots` returns early with `todo` empty before
any load, `data_manager.py:3179-3181`); only the multi-date backfill still pays it.

Note the dev handoff's phrasing "every symbol loaded 3 times" describes the *mode*, not the max (11);
the reviewer's report carries the corrected figures.

**B4 — GAP (disclosed): item 2's bound is ~4%, not an architectural bound**

`compute_drawdown_expectations` (`apps/backend/app/engine/forward_testing.py:2330-2341`) chunks the
`stored_by_key` read, but the built dict's final size is unchanged, and `compute_samples`'s own
untouched 771,662-row materialization dominates the call. Measured 1,215,052 KB → 1,165,092 KB peak
RSS. This is disclosed exactly as the spec's NOTES section requires (split record, not a rounded-away
residual) in the dev handoff, in `reports/perf-budgets.md:4500-4530`, and in the test module's own
docstring. I re-ran the drill: **3 passed** — the reference aborts and the shipped code completes at
the same tight cap, the generous control cap passes both, and the starved cap makes the shipped code
degrade honestly (caught `MemoryError`, `SUBSEQUENT_READ_OK`, never a crash or wedge). The discriminating
window (1,210,000–1,220,000 KB) is narrow and host-calibrated, but the module carries a control
assertion so a miscalibration fails loudly rather than passing silently.

**B5 — GAP: `_excluded_counts_by_date` double-counts a duplicated snapshot date**

`apps/backend/app/engine/data_manager.py:592-612`. `totals` is keyed by date, so a duplicate in
`dates` collapses to one key while the inner `for d in dates` loop still increments it once per
occurrence per batch — the pre-fix code produced two independent points each with the correct tally.
**Unreachable in production**: `ScannerRun.asof_date` is `Field(index=True, unique=True)`
(`apps/backend/app/models.py:204`) and the only production caller derives `dates` from
`select(ScannerRun.asof_date)`. Recorded because it is a genuine divergence from the pinned reference
for any future caller that passes a non-unique date list; not fixed (unreachable, and the fix would
touch point ordering for no live benefit).

**B6 — OBSERVATION: `read_pool()` is re-read from disk once per (batch × date)**

`resolve_with_reasons` calls `read_pool(seed_dir)` (`universe_screen.py:86-102`, an uncached CSV file
read + parse) on every invocation. Batching multiplies that by the batch count: at the shipped width
against the live 548-symbol pool and 1,880 snapshot dates, a cold membership compute now issues
~20,680 `read_pool()` calls plus 11× the full-pool sort/filter, versus 1,880 before. Small next to the
dominant per-(symbol, date) `bars_asof` work, which is unchanged, but a real added constant on the
cold path.

**B7 — OBSERVATION: stale docstring contradicts the shipped code**

`membership_timeline_cached` (`apps/backend/app/engine/data_manager.py:650-654`) still states
"`_membership_timeline` runs its per-date loop inside a `prefilled_bar_cache` (one query loads every
symbol's full series)". That is exactly what this iteration removed. In a codebase this dependent on
docstrings as design record, a future reader will be misled.

**B8 — OBSERVATION: the candidate pool is 548 symbols, not 591**

`reports/perf-budgets.md:4466` and the dev handoff both describe the live basis as "591 symbols". 591
is `symbol_count` (distinct priced symbols, including ETFs and `^VIX`); `read_pool()` returns **548**,
which is what the bound actually scales with. The same perf-budgets paragraph reports "11 batches
observed" — consistent with 548/50, not with 591/50 (which is 12). Confirmed live: `/api/data` serves
`candidate_pool_count: 548`, `symbol_count: 591`.

**B9 — OBSERVATION: the browser-QA run left a backend process alive at the memory cap**

PID 2944679 is still running with `VmPeak: 6,291,352 kB` — 104 KB under the 6,291,456 KB cap — holding
4.1 GB RSS. This matches UT-12's own recorded note (a `MemoryError` in
`_regime_lab_members_by_horizon`, `research.py:3339`, with the endpoint still returning 200). That
accumulator is a different call site from either fix and is explicitly out of scope, but the leftover
process is worth reaping before the next iteration measures anything on this host.

### Frontend Findings

**F1 — OBSERVATION: three of the four Retry controls were verified by inference, not by clicking**

UT-03 (factor-lab), UT-06 (phase-severity-lab) and UT-08 (regime-phase-factor) are recorded PASS with
"Retry-click … NOT directly observed"; only UT-11 (severity-velocity) actually clicked Retry and
observed a clean re-entry into a single fresh error card. I read all four wirings rather than trust
the inference: `FactorLabPage` (`_labs.tsx:286`), `PhaseSeverityLabPage` (`_labs.tsx:4564`),
`RegimePhaseFactorPage` (`_labs.tsx:4915`) and `SeverityVelocityPage`
(`severity-velocity/page.tsx:69`) each add `attempt` to the fetch effect's dependency array and each
increments it from the retry control — byte-for-byte the pattern proven for `RegimeLabPage`
(`_labs.tsx:4257`). The inference is sound; recorded as an evidence-quality note, not a defect.

**F2 — OBSERVATION: the "computing" state was directly observed on 1 of 5 labs**

UT-02, UT-07 and UT-10 are SKIPPED because their endpoints were already warm and Chrome MCP offers no
network throttle. UT-05 (phase-severity-lab) *did* capture it end-to-end on a genuine ~1m45s cold
compute — exact copy match, a visibly ticking counter (20s → 1m 33s), backend CPU confirmed active —
and UT-12 confirmed Regime Lab's unchanged behaviour. Since `resolveLabLoadPanel` is a shared pure
function with 13/13 tests and all four pages call it identically, one direct observation plus four
identical wirings is adequate; the three skips are honestly recorded rather than papered over.

### Test Findings

**T1 — OBSERVATION: the "`git show HEAD`-pinned" references are hand-transcribed, not extracted at
test time**

Both reference oracles (`test_membership_timeline_batch_bound.py:71`,
`test_forward_testing.py:_reference_compute_drawdown_expectations`, and the child-probe copy in
`test_evidence_drawdown_memory_pressure.py:95`) are pasted copies, not `git show HEAD` output read at
runtime. I diffed the membership one against `git show HEAD:apps/backend/app/engine/data_manager.py`
(lines 495-560) and it is verbatim modulo comments and type annotations — so the iter-32 lesson's
*intent* is honoured. The residual exposure: both references call the **current**
`universe_resolver.resolve_with_reasons` and `_membership_labels`, so a defect introduced into the
resolver's `symbols=None` default path would be invisible to TC-2 (both sides would share it). Now
mitigated — the test added under B1 exercises that exact default path against the independent no-cache
branch.

**T2 — OBSERVATION (verified, no action): the new B1 oracle is live, not vacuous**

An equivalence oracle can pass by accident, so I negative-controlled it. A −1 perturbation of the
cached `trailing_count` was **not** detected (correctly — the prefilter count only matters when it
crosses the history gate, and `resolve_candidate` recomputes `bars` from the series). Two perturbations
that model the real failure modes were both detected: forcing one symbol's cached `trailing_count` to
0 (gate-crossing) → detected; dropping the last bar from the cached `bars_asof` (content divergence) →
detected. Recorded so a future reader knows the oracle's sensitivity boundary.

---

## 3. Domain Assessment

The core domain question is whether bounding *how* bars are loaded changed *what* the engine computes.
It did not, and now that is proven rather than asserted.

`_excluded_counts_by_date` (`data_manager.py:568-612`) is the right shape. Its two-branch design is
honest about scope: an outer job-scoped cache (`_do_backfill`, `_persist_per_date_coverage_snapshots`)
is reused unchanged, and only the standalone entry point batches. The summing-across-disjoint-batches
argument holds because `resolve_candidate` (`universe_resolver.py:83-119`) is a pure per-symbol
classification with no cross-symbol interaction, and `excluded_counts` is initialised from the same
`EXCLUSION_REASONS` tuple in both the old inline `dict(diag["excluded_counts"])` and the new
pre-seeded `totals[d]` — so even Python dict key *order* is preserved, which byte-identity of a
JSON-serialised cache payload actually requires. `_BarCache.load_only` (`prices.py:164-205`) is
correctly independent of `prefill`'s `_prefilled` re-entrancy guard, correctly records a zero-bar
symbol as an empty series (matching `prefill`'s `expected_symbols` bookkeeping so a no-bar candidate
still resolves to `below_history` with no extra query), and is only ever driven by one serial loop, so
the "no lock needed" claim holds.

I checked the boot-warm-up concern directly, because a plain `bar_cache` context anywhere upstream
would silently make the whole bound inert: `warmup._run_warmup` does hold `with bar_cache(session)`
(`warmup.py:173`), but `_warm_membership_timeline` and `_warm_coverage_snapshot` are called *after*
that block and each opens its own session on the engine (`warmup.py:114`, `warmup.py:132`), so
`active_bar_cache` is `None` and the batched path applies. `readiness._cached_warmup_dates`'s
`bar_cache` is scoped to `_warmup_dates` alone. The bound is real on the paths the spec names.

`compute_drawdown_expectations`'s chunking is correct and byte-identical for a reason the tests do not
state: `stored_by_key` is consumed only through `.get(...)` (`forward_testing.py:2358`), never
iterated, so the changed insertion order across chunks cannot affect output; and the chunks partition
by ticker, so a duplicate `(symbol, asof_date)` pair — were one possible — would still land in the
same chunk. The isolate-and-continue guard in `evidence.py` is genuinely untouched, and the TC-8 drill
exercises the real `compute_drawdown_expectations_cached` entry point with a fresh DB copy per probe
so an earlier success cannot turn a later probe into a trivial cache hit. That is careful test design.

The frontend is exactly what the plan asked for: mechanical, no new logic, `resolveLabLoadPanel`
untouched (13/13 still green), and `RegimePhaseFactorPage` correctly kept its own
`CombinationSkeleton` + inline error card rather than being forced onto `ResearchError`/`LabSkeleton`,
preserving its test-id contract while gaining the same semantics.

Where the work is weakest is not the code — it is the evidence chain around J-07. The backend fixes
are proven at unit and live-DB level, but the journey they exist to serve has no browser-QA row this
iteration, and the QA report's PASS reads stronger than the artifacts underneath it.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_membership_timeline_batch_bound.py` | Added `test_coverage_payload_bar_readers_byte_identical_with_and_without_outer_cache` (+ two import lines) — the missing coverage-payload half of TC-2: pins `resolve_with_reasons` and `_trading_days` byte-identical between the pre-fix (bar-cache-active) and shipped (no-cache) branches on the live seed DB, bounded to one shipped-width batch at a time. Finding B1. |

No production code was modified. `git status` confirms the only file I touched is the (untracked,
new-this-iteration) test module; the diff is one test function plus the imports it needs.

### Verification evidence (all commands run under the AG-10 host-guard mask, `taskset -c 0-3,8-11`, BLAS/OMP capped to 4)

```
apps/backend $ pytest tests/test_membership_timeline_batch_bound.py -q -p no:randomly
  4 passed in 175.49s
  [perf-budgets] _membership_timeline peak tracemalloc bytes —
    reference (unbounded, pre-fix): 1,125,619,032 | shipped (batch_symbols=50): 329,751,464
    | reduction: 70.7%
```
The new test alone: **1 passed in 44.86 s** (16 resolver comparisons + the 5,383-date calendar, 0
divergences). The printed TC-1 figures independently reproduce the dev's reported 1,125,618,771 →
329,751,051 / 70.7% to within a few hundred bytes, so TC-1, TC-2 and TC-3 are confirmed first-hand.

Negative control for the new oracle (finding T2), run as a standalone probe against the live seed DB:
```
(a) gate-crossing trailing_count perturbation detected: True
(b) bar-content perturbation detected: True
```

Other suites re-run first-hand:
```
pytest tests/test_data_manager_membership_cache.py tests/test_bar_cache.py -q
  1 failed, 25 passed in 127.76s
  (the single failure is the pre-existing test_kdate_backfill_loads_each_symbol_at_most_once —
   assert 10 == 1, typical per-symbol count 2 — finding B3)
pytest tests/test_forward_testing.py -k drawdown -q      → 26 passed in 580.68s
pytest tests/test_evidence_drawdown_memory_pressure.py -q → 3 passed in 213.58s   (TC-8)
apps/frontend $ npx tsc --noEmit -p tsconfig.json         → 0 errors
apps/frontend $ npx tsx lib/lab-load-panel.test.ts        → 13 passed
```

Live backend evidence for finding B2 is tabulated in §2 (booted via `scripts/start-backend.sh`,
stopped cleanly afterwards; port 8255 released).

### Definition of Done

Items 1, 4 and 5 got the full code trace (risk class: memory safety and persisted-payload identity;
plus artifact contradictions). Items 2, 3 and 6 are accepted on the reviewer's PASS plus executed
QA/replay rows, cited below.

| # | DoD item | Status | Evidence |
|---|----------|--------|----------|
| 1 | J-07 passes via browser-qa-agent | **NOT MET** | No J-07 row in the merged UI results; UT-13/UT-14 SKIPPED (`…ui-test-results.llm.md:239-249`); `status.json: browser_checks_run=false`. Partially closed by hand — §2/B2 |
| 2 | J-06 passes; 4 sibling labs render the shared computing/error/retry states | MET | Reviewer PASS_WITH_NOTES, no frontend issue filed; UT-01/03/04/05/06/08/09/11/12 PASS with screenshots (UT-05 captured the computing card with exact copy + ticking counter); 3 computing-notice skips are warm-cache artefacts (F2); wirings re-read in code (F1) |
| 3 | J-01/03/04/05/08/09 remain green via deterministic golden replay | MET | `reports/phase-goal-ops-hardening-iter-36-regression-replay-results.md` — 6/6 PASS, 0 FAIL, per-journey screenshots |
| 4 | No anti-goal violation; iter-29/d and iter-35/k closed, or residual stated explicitly | MET (via the residual clause) | AG-10 launch blocks intact in `scripts/start-backend.sh`; AG-3 checked live (`/api/data` internally consistent, `/api/evidence` real figures); AG-5 untouched (no scoring/return path changed); residuals stated — B3, B4 |
| 5 | Unit tests pass; bound proven on the REAL basis; pinned oracle proves byte-identical coverage **and** membership-timeline output; drawdown payload byte-identical; no regression in the `_BarCache`/`bars_asof`/`bars_after`/`trailing_count` suites | MET **after** the audit fix | Coverage half was missing (B1) — added and passing; membership half, TC-1/TC-3 and TC-8 reproduced first-hand above; 25/26 in the bar-cache suites, the one failure pre-existing and improved (B3) |
| 6 | Dev handoff written | MET | `docs/handoffs/goal-ops-hardening-iter-36-dev.md` (+ a frontend handoff) — accurate, with honest Known Issues |

---

## 5. Recommended Next Step

Proceed — but do **not** let J-07 be recorded as `passing` from this iteration's evidence. Its status
is `unknown`: the browser-QA lane never ran it, and what I closed by hand (`/data` and `/evidence`
serve correct values, `/api/health` 200 at 1 Hz, VmPeak at 42.8% of cap) does not cover the
full-horizon forward-aggregate warm or the induced-pressure drill the DoD names.

Concretely, for iter-37:

1. **Re-run J-07 in the browser-QA lane** with the backend restart permission the agent was denied
   this time (`…ui-test-results.llm.md:241-245` — three `scripts/start-backend.sh` attempts blocked).
   That single environment fix unblocks UT-13, UT-14 and TC-4 together. Order the test plan so
   backend-down tests run **last**, so a denied restart can no longer strand the tests behind them.
2. **Carry `_persist_per_date_coverage_snapshots`' whole-table prefill (B3) as the next ledger item**
   — it is the last unbounded whole-table load on the ingest warm chain and the only thing standing
   between the current state and J-07's Acceptance clause being fully met. It is also what keeps
   `test_kdate_backfill_loads_each_symbol_at_most_once` red.
3. **Two one-line hygiene fixes** deliberately left undone here as out-of-scope: the stale
   `membership_timeline_cached` docstring (B7) and the 591-vs-548 pool figure in `perf-budgets.md`
   (B8).
4. **Reap PID 2944679** (B9) before any measurement pass on this host — it is holding 4.1 GB RSS at
   the memory cap.

The iteration's substance is sound and the system is materially stronger than before it: the peak
memory of the coverage cold-compute is down 70.7% with byte-identity now proven on both halves of the
payload, and four research labs stopped lying to users about whether they were working or broken.
