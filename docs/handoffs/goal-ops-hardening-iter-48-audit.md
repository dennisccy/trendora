# goal-ops-hardening-iter-48 Audit Report

**Date:** 2026-08-05
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The engineering in this iteration is sound and well-proven: J-05's O(dates × pool) resolver storm is
genuinely closed (9.18 s / 24.10 s / 21.01 s across three independent live runs, down from an
extrapolated hour-plus) and the `samples.py` `total`/`regime` AG-8 bound is correct and thoroughly
tested. But the phase's stated GOAL — *"a historical-day backfill actually finishes; its run reaches a
real terminal outcome instead of sitting on `running` forever"* — was **not delivered**: the browser-QA
lane's own live drill (job `0ce8e2fb0bd94e52ac3c191080ace831`, target `2012-06-15`) never reached a
terminal status, and `data_provider_runs` id 308 is still `status: "running"`, `finished_at: NULL` in the
committed DB right now. Three DoD bullets are unmet (the J-05 acceptance, the required-still-passing
replay set, and the "new tests green" bullet), the merged journey lane's own verdict is **FAIL**, and
this iteration's two target journeys (J-05, J-07) plus required journey J-04 have **zero executed rows**
in any lane. The residual blocker is bigger than disclosed — `forward_aggregates_warm` alone measured
1,334 s on the live run, exceeding TC-1's entire 1,200 s bound on its own — which is a decision for the
next iteration, not something an audit fix can close.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (gap — cannot be fixed in this audit): the historical-gap backfill still never terminates; the phase's headline capability is not delivered.**

`apps/backend/app/engine/data_manager.py:3840-4127` (the finalize tail) / live evidence.

The spec's "New user-facing capability" is: *"A historical-day backfill … reaches a real, honest outcome
— success or a named failure reason — instead of appearing to run forever."* The only end-to-end
verification of that capability against the shipped build is the browser-QA lane's UT-02 run, and it
failed. Traced through the primary evidence rather than the handoff:

- `logs/backend.log`, job `0ce8e2fb0bd94e52ac3c191080ace831` (target `2012-06-15`, started 22:50:27 UTC):
  `coverage_membership_timeline_refresh=21.01s` → `per_date_coverage_warm=7.05s` →
  `market_phase_warm=28.02s` → **`forward_aggregates_warm=1334.13s`** → `research_hot_keys_warm=39.73s`
  → `index_series_warm=0.05s` → `drawdown_expectations_warm` **never logged** (still running when the
  backend was stopped ~10 min later).
- Live DB read (`apps/backend/data/trendora.db`, `data_provider_runs` id 308): `status: "running"`,
  `finished_at: NULL`, message `{"kind":"backfill","start":"2012-06-15","end":"2012-06-15",
  "snapshots_created":1,…}`. The row is still non-terminal as of this audit.
- `reports/phase-goal-ops-hardening-iter-48-ui-test-results.md:24` (UT-02, **FAIL**): terminal status
  "never reached within 31+ min"; `aggregates_refreshed` stayed `[]` throughout.

`forward_aggregates_warm` **alone** (22 min 14 s) exceeds TC-1's whole 1,200 s bound. This defeats the
phase's primary purpose, so it is CRITICAL by the severity tree — but bounding two unrelated
finalize-tail phases is explicitly out of this iteration's scope and is a full iteration of work, so it
is reported, not fixed.

What this finding does **not** say: the fix itself is bad. `coverage_membership_timeline_refresh` — the
exact phase this iteration diagnosed and fixed — measured 9.18 s, 24.10 s and 21.01 s across three live
runs on three different target dates. That defect is genuinely closed. The job is now blocked by
different, pre-existing phases.

**B2 — IMPORTANT (fixed): the disclosed root cause of the TC-1 miss was incomplete, and would have misdirected the next iteration.**

`docs/handoffs/goal-ops-hardening-iter-48-dev.md:166-188` and `reports/perf-budgets.md` (Item R table
row + Addendum 1) both attribute the TC-1 miss to `drawdown_expectations_warm` alone, and describe
`forward_aggregates_warm` as an ordinary "same per-horizon warm every ingest pays" cost. That was
written from two samples (102.48 s, 153.07 s). The third live run measured **1,334.13 s** — a 13x spread
across three runs of the same phase, and on its own over the TC-1 budget. The handoff's explicit
recommendation ("score J-05 as root-cause-fixed … because of a cost this iteration did not touch",
singular) understates the remaining work by roughly a factor of two in the number of phases that need
bounding.

*Fix applied:* an "AUDIT CORRECTION" bullet in the dev handoff's Known Issues and "Addendum 2" in
`reports/perf-budgets.md`, both recording the third run's full phase table, the 102 s → 153 s → 1,334 s
spread, and the still-`running` row 308. No product code touched.

**B3 — GAP: `_membership_bars_are_forward_only`'s count arithmetic can be defeated by a compensating bar removal + insertion below the previous max bar date — and this iteration adds a second caller that relies on it.**

`apps/backend/app/engine/data_manager.py:719-726`.

The proof is `(cur.bar_count - prev.bar_count) == count(bars > prev_max_bar_date)`. Remove *K* bars at or
before `prev_max_bar_date`, add *K* back at or before it, and add *M* after it, and the arithmetic still
balances while historical bars *did* move — invalidating the reused `excluded` tallies. This is a
pre-existing weakness in the iter-45 audit-B4 helper (its own docstring claims "any bar removal … returns
False", which the arithmetic does not actually guarantee), not introduced here. It matters slightly more
now because iter-48 makes it the gate for a *second*, wider call site (`:914-916`, the gap-insert
branch — which unlike append-forward can fire for any date ordering). Not fixed: it requires a real
manifest/checksum design decision, and no code path in this codebase removes bars below the max today.

**B4 — OBSERVATION: the two `_factor_samples` branches now resolve config inconsistently.**

`apps/backend/app/engine/samples.py:171` calls `_factor_observations(session, factor, horizon, as_of)`
with no `cfg`; `:182` calls `_factor_regime_observations(…, cfg=cfg)`. Pre-fix both went through the
no-`cfg` path. I verified this cannot change results: `cfg` only supplies `read_batch_size` and
`factor_join_run_chunk`, and since `runs_with_fr` is sorted and chunks are contiguous and non-overlapping
with per-chunk `ORDER BY (run_id, id)`, the concatenated output is globally `(run_id, id)`-ordered for
any chunk width. Cosmetic inconsistency only.

### Frontend / Journey-Verification Findings

*(`Frontend Present: no` — no frontend code changed. These concern the journey-verification instruments.)*

**F1 — IMPORTANT (fixed): J-05's golden was burned again, by the very lane run that was meant to score it.**

`runs/goal-session-ops-hardening/journey-scripts/J-05.json`.

The iter-47 audit's P2 finding was that this golden decays into a null test after its first productive
run. The dev applied the TC-9 fix and rotated the target to `2012-06-15`, and the plan explicitly warned
to "rotate its target date if `2011-01-05` gets consumed by this iteration's own TC-1 drill". The drills
avoided it — but the browser-QA lane's UT-02 job then ingested `2012-06-15` itself. DB confirmation:
`scanner_runs` now holds row id 2906 for `asof_date='2012-06-15'`. The next run of this golden would be a
zero-work job (`snapshots_created: 0`), the card would read "0 snapshots", and step 8's `"1 snapshots"`
assertion would fail — i.e. the golden is dead for its own target, for the second consecutive iteration.

*Fix applied:* rotated all five date references to `2012-01-05`, verified against the live DB as
genuinely unsnapshotted (`scanner_runs` count 0) with 481 symbols carrying bars on that date, and
re-validated the file as JSON (10 steps).

**F2 — GAP: the golden's positive-work assertion is page-wide text, and the replay schema cannot express a scoped one.**

`incredible_auto_dev/scripts/automation/lib/demo_runner.py:912-922`: `_check_expect` tests `"text" in exp`
**before** `"target" in exp`, so whenever a step carries `text` the `target` is ignored entirely — a
testid-scoped text assertion is not expressible. Step 8's `{"type":"expect","text":"1 snapshots"}` is
therefore matched page-wide, and Playwright's `get_by_text` is substring-based, so "11 snapshots" or
"431 snapshots" would also satisfy it.

I verified statically that TC-9's negative property nonetheless holds on `/data`: the only two renderers
of the string "*N* snapshots" are the live job card (`apps/frontend/app/data/page.tsx:2785`) and
`LastRunSummary` (`:2629`), and `LastRunSummary` renders only when no job started this browser session —
which is never true during a replay. The run-history table (`:3538`) renders a bare number with no
"snapshots" word. So on a zero-work run the card reads "0 snapshots" and the step fails, as TC-9
requires. Not fixed: making this airtight needs a dedicated testid on the count, i.e. a frontend change
this iteration's spec excludes.

**F3 — IMPORTANT (gap): TC-7's "full 8-journey pass" did not happen, and TC-8/TC-9 were never executed.**

`reports/phase-goal-ops-hardening-iter-48-ui-test-results.md` — headline **Browser QA Verdict: FAIL**:

- *Missing target journeys*: `UT-J-05`, `UT-J-07` — "no test case executed … by any lane". Both are this
  iteration's own `Target journeys`.
- *Missing required journey*: `UT-J-04` — recorded as `DEFERRED-BUDGET`, "not run this iteration".
- `UT-03`, `UT-07`, `UT-08` SKIPPED (UT-07: the Factor Lab's first-read compute had not finished after
  26+ min — the very page whose cohort reads this iteration bounded).
- J-05's golden — rebuilt this iteration specifically for TC-9 — was **never executed**, so TC-9 has no
  empirical result. TC-8 (reading each replay script's own JSON content, not just its PASS row) has no
  artifact showing it was performed.

The one part of TC-7 that *does* hold is the sequencing: newest `apps/` mtime 22:48:44, replay results
23:09, merged results 00:23 — no product code changed after the lane ran. This is the third consecutive
iteration this requirement was written into the spec, and the third consecutive iteration it came out
incomplete.

### Test Findings

**T1 — IMPORTANT (fixed): TC-2's byte-identity proof was vacuous — it could not detect a mis-keyed reuse.**

`apps/backend/tests/test_data_manager.py:5737-5756`
(`test_historical_gap_fill_reused_excluded_byte_identical_to_full_recompute`).

The `membership_fast_path_engine` fixture (`:5537-5547`) creates three snapshots and **zero**
`DailyPrice` rows, so `resolve_with_reasons` returns the identical constant tally for every date. The
bounded reuse path's whole job is to map each cached date's tally back onto *that* date — but with all
tallies equal, any mis-keying compares equal to the oracle. TC-2 is an explicit acceptance criterion of
this phase and its unit proof did not exercise the discriminating dimension.

*Fix applied and mutation-proven:* added
`test_historical_gap_fill_reuse_is_keyed_per_date_not_vacuously_identical`, which stubs the resolver to
return a tally derived from the date, then asserts (1) the per-date tallies are genuinely all-distinct
(an anti-vacuity guard that fails loudly if a refactor flattens them again), (2) the bounded path
actually engaged (resolver ran for the new date only, snapshotted before the oracle call), and (3)
byte-identity against the full oracle.

Verification, per the audit's own evidence rule:

```
# with a deliberate mis-keying mutation injected into data_manager.py:580-583
#   (reuse_excluded_by_date[d]  ->  next(iter(reuse_excluded_by_date.values())))
$ .venv/bin/python -m pytest tests/test_data_manager.py -k "historical_gap_fill" -q -p no:randomly
-> 1 failed, 5 passed
   FAILED …::test_historical_gap_fill_reuse_is_keyed_per_date_not_vacuously_identical
   (the pre-existing byte-identity test PASSED under the mutation — confirming the vacuity)

# mutation reverted (file diff'd byte-identical to its pre-mutation copy), full selection:
$ .venv/bin/python -m pytest tests/test_data_manager.py \
    -k "historical_gap or gap_fill or gap_insert or append_forward" -q -p no:randomly
-> 11 passed in 2.30s
   (includes the iter-45 correctness pin
    test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse — assertions unmodified —
    the append-forward suite, and the new error-isolation test)
```

**T2 — IMPORTANT (gap): three tests are failing on this build; only one reaches the handoff's Known Issues.**

1. `test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound` — committed FAILING by
   design as an honest signal (disclosed; reviewer asked for `xfail(strict=False)`).
2. `test_membership_timeline_batch_bound.py::test_peak_memory_reduced_vs_pinned_reference_on_live_seed` —
   FAILING (28.5 % vs its `>= 30 %` iter-36 threshold). Disclosed **only** inside `perf-budgets.md`
   Item R; absent from the handoff's Known Issues, from `status.json`, and from the QA report. I
   independently agree it is not caused by this diff: it exercises `_excluded_counts_by_date`'s
   no-outer-cache branch, and its three-positional-argument call takes the `reuse_excluded_by_date=None`
   path this iteration left byte-identical.
3. `test_starved_cap_shipped_still_degrades_honestly_never_crashes` — FAILED in QA's own run (see T3).

The DoD bullet "new tests from TESTING REQUIREMENTS added and green" is therefore unmet as written.
*Fix applied (disclosure only):* #2 and #3 added to the dev handoff and to `status.json`'s `known_gaps`.

**T3 — IMPORTANT (gap): the QA report reached PASS_WITH_NOTES on incomplete evidence and skipped the journey lane on a category error.**

`reports/qa/goal-ops-hardening-iter-48-qa.md`:

- Header reads "**Status:** in progress (backend test suite running)" and the results section
  "Running - 96% progress at last check" — a verdict was issued before the run finished (`:34`, `:42`).
- It simultaneously reports "270 tests collected; 270+ passing" *and* one FAILED test, then dismisses
  the failure as "likely environmental flake … Memory-pressure tests can be flaky" (`:185`, `:192`) with
  no diagnosis. I can rule this diff out as the cause — the `decile` branch is byte-identical in it
  (`samples.py`'s `else` row-comprehension is the unchanged pre-fix code, and
  `_factor_decile_observations` is untouched) — but the failure itself remains undiagnosed, and "flake"
  is an inference, not evidence. (Circumstantial: the deterministic replay lane was driving live backfill
  jobs at 23:08-23:09 while QA's `ulimit -v` subprocesses ran under a 150 s timeout.)
- `:74-78` records "**Browser-Based Verification: SKIPPED — backend-only phase**". `Frontend Present: no`
  means no frontend *code* changed; it does not exempt the iteration from the DoD's 8-journey
  browser-qa/replay pass, which is bullets 1, 3 and 4 of the DoD and the whole of TC-7/TC-8/TC-9. The
  lane did run later, separately, and returned FAIL — QA's verdict never saw it.
- `:127-132` quotes a `status.json` `blockers` array containing an entry; the file as written carried
  `"blockers": []`.

*Fix applied:* `status.json` now carries three real `blockers` (the non-terminal run 308, the lane FAIL
with its missing target/required journeys, and the unexecuted TC-8/TC-9), `browser_checks_run: true`,
`browser_qa_verdict: "FAIL"`, and `audit_verdict: "FAIL"`, so the evaluator reads the lane's actual
result rather than an unqualified PASS_WITH_NOTES.

---

## 3. Domain Assessment

**The J-05 fix is correct.** I traced it rather than trusting the handoff. `membership_timeline_cached`
(`data_manager.py:914-922`) fires the new branch only when `payload is None and new_dates and not
missing_dates and _membership_bars_are_forward_only(...)`, and rebuilds
`reuse_excluded_by_date` from the previous payload's `points[*]["excluded"]` — which is
`excluded_by_date[d]` verbatim (`:594-600`), the same shape `_excluded_counts_by_date` returns, so the
JSON round-trip is lossless. `_membership_timeline` (`:574-585`) resolves only
`[d for d in dates if d not in reuse_excluded_by_date]` and reuses the rest, while `entries`/`exits`/
`size` are recomputed fresh for every date in full ascending order from `members_by_date` — the
order-dependent iter-27/iter-9/iter-45 invariant is untouched, and `_membership_timeline_incremental`
and the `append_forward` gate are byte-for-byte unmodified as the spec required. The safety argument
holds: `resolve_with_reasons(session, d, cfg)` reads only bars ≤ *d*, the pool and the config, so an
unrelated snapshot date's insertion cannot change it; the only invalidators are `min_history_bars` and a
bar landing at/before a cached date, which is exactly what the reused gate checks (subject to B3).
`freshly_resolved[d]` cannot `KeyError` because `_excluded_counts_by_date` pre-seeds `totals` for every
date it is given.

**The `samples.py` bound is correct.** `_factor_regime_observations` (`research.py:329-388`) reproduces
`_factor_observations`'s chunked walk with the regime predicate applied before the accumulator append;
its chunk-skip shortcut is sound (a chunk with no in-regime run contributes zero rows either way);
ordering is preserved because chunks are contiguous over sorted `runs_with_fr` with per-chunk
`ORDER BY (run_id, id)`. The `total` branch's in-place rebuild (`samples.py:192-201`) is safe: `members`
is never read after `rows = members`, and `cohort` does not reference it. Test coverage here is genuinely
strong — pinned pre-fix reference across both fixture regimes and both all-history/as-of scopes,
union-covers-the-pool, chunk-independence, a non-materialization proof, an honest-empty case, and TC-6's
8/8 including 5/5 per variant.

**The gap between component and outcome is the story of this iteration.** Two well-engineered,
well-tested fixes landed; neither closes the user-visible journey they were aimed at, because the
finalize tail's other phases were never in scope and turn out to dominate. The handoff and perf-budgets
were honest about *that this happened* and imprecise about *why* (B2). The verification lane that was
supposed to settle it — for the third consecutive iteration — came out incomplete (F3).

---

## 4. Fixes Applied During This Audit

No product code (`apps/backend/app/**`, `apps/frontend/**`) was modified — verified: the `app/` diffstat
is unchanged from the developer's (`data_manager.py` +123, `research.py` +62, `samples.py` +54).

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_data_manager.py` | Added `test_historical_gap_fill_reuse_is_keyed_per_date_not_vacuously_identical` — a date-keyed resolver stub makes every date's `excluded` tally distinct, so TC-2's byte-identity claim actually discriminates a mis-keyed reuse. Mutation-proven (T1); 11/11 green after revert. |
| 2 | Important | `runs/goal-session-ops-hardening/journey-scripts/J-05.json` | Rotated the target date `2012-06-15` → `2012-01-05` (5 refs). `2012-06-15` was consumed by this iteration's own browser-QA lane (`scanner_runs` id 2906), which would have made the golden fail on its next run. New date verified unsnapshotted with 481 symbols of bars. |
| 3 | Important | `docs/handoffs/goal-ops-hardening-iter-48-dev.md` | Added an AUDIT CORRECTION superseding the single-phase attribution of the TC-1 miss (records `forward_aggregates_warm=1334.13s`, the 102/153/1334 s spread, and the still-`running` row 308), plus the previously-unlisted failing `test_membership_timeline_batch_bound` test. |
| 4 | Important | `reports/perf-budgets.md` | Appended "Addendum 2" with the third live run's full phase table and the two corrections it forces (fix confirmed a third time; residual is ≥2 unbounded phases, not 1). |
| 5 | Important | `runs/goal-ops-hardening-iter-48/status.json` | Replaced the empty `blockers` with the three real ones; set `browser_checks_run: true`, `browser_qa_verdict: "FAIL"`, `audit_verdict: "FAIL"`; expanded `known_gaps` with the corrected attribution and the two undisclosed test failures. |

**TC-7 note (honest disclosure):** changes 1-5 are test-only, journey-script and documentation changes —
no runtime behaviour changed, so the lane's executed rows remain valid for the shipped build. A
mechanical newest-mtime check that includes `apps/backend/tests/**` will nonetheless now trip. Given the
FAIL verdict the lane must be re-run next round regardless, so this is disclosed rather than worked
around.

---

## 5. Recommended Next Step

Do **not** score J-05 as closed. Recommended order for iter-49:

1. **Bound `forward_aggregates_warm` first** — it is the newly-identified dominant blocker (1,334 s
   observed, 13x variance across three runs) and was not on anyone's list before this audit. Instrument
   its per-horizon loop the way iter-48 instrumented the finalize tail, then bound it. `data_manager.py:
   3962-4001`.
2. **Then `drawdown_expectations_warm`** (`:4091-4127`) — the previously-named residual, 667 s in the one
   run that completed, unbounded in two others.
3. **Only then re-run J-05's golden**, now rotated to `2012-01-05` and unconsumed. Confirm the target is
   still unsnapshotted immediately before the run, and treat TC-9 (the golden must FAIL on a zero-work
   job) as an executed check, not a static argument — this audit could only verify it by reading.
4. **Make the journey lane's completeness a hard gate.** Three consecutive iterations have now shipped
   with target journeys carrying zero executed rows while upstream gates read green. The merged results
   file already prints "Missing Target Journeys"; nothing consumes it. A run where `Target journeys` have
   no executed row should not be scoreable.
5. Carried, unchanged: the Regime Lab 8192 MB hit (15th deferral), the shared warm-in-progress sentinel,
   J-09's background-worker visibility, the health-poll ≤2 s ceiling, and B3's forward-only bar proof.

Cheap follow-ups worth doing whenever the file is next open: mark the deliberately-failing
`test_start_backend_historical_gap_insert_…` as `xfail(strict=False)` (the reviewer's MINOR note), and
re-calibrate or retire `test_membership_timeline_batch_bound`'s stale 30 % threshold.
