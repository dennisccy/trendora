# goal-ops-hardening-iter-53 Audit Report

**Date:** 2026-08-08
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's goal was genuinely achieved: both named finalize-tail phases were profiled (not
guessed), bounded with pre-existing already-proven accessors, and re-measured with Addendum 14's own
methodology — `coverage_membership_timeline_refresh` and `market_phase_warm` each went from producing a
connection-level `/api/health` non-answer to **zero**, `market_phase_warm` dropped 26.26s → 0.73s, and
the residual non-answer that relocated to an untreated neighbour plus the **worse** 1,559.30s
finalize-tail total were both disclosed rather than minimised. AG-8/AG-9/AG-10 all hold under my own
independent re-verification, and J-04 steps 3-5 finally have real first-capture evidence.

Two IMPORTANT gaps remain. (1) The market-phase "byte-identical" claim is **provably false as stated** —
the count-bounded fetch is one bar narrower than the calendar filter it feeds, which I demonstrated
flipping the served phase label from `Correction` to `Pullback` on the iteration's own fixture; it is
harmless at the committed config only because real trading-day density leaves a wide margin (measured).
(2) The QA report's TC-6 PASS cites evidence that does not show J-04 and predates the actual J-04
evidence by ~45 minutes, and its `PASS` silently overrides the browser lane's own `BLOCKED` verdict.

**No fix was applied, by design.** This spec's DoD item 5 / TC-7 is a binding sequencing rule: *"if the
audit step subsequently finds a defect needing a product-code change, it is filed as a note for iter-54
rather than applied as a code-changing audit-fix, so this iteration's own lane evidence stays valid for
the tree it measured."* Every finding below that would require touching `apps/backend/**` is therefore
filed for iter-54. I confirmed the freeze held: newest `apps/backend/**` mtime `07:05:37`, earliest lane
artifact `08:29:30`; my own work touched no repository file.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — filed for iter-54): the market-phase bounded-window fetch is off by one bar; the "byte-identical" proof in the code comment, the dev handoff and Addendum 15 is false as stated.**

`apps/backend/app/engine/market_phase.py:217` (`_severity_reading`) and `:554`
(`_trailing_ma_reclaimed`) both changed to:

```python
start  = d - timedelta(days=mp.lookback_days)
window = [bar for bar in bars_asof_window(session, bench, d, mp.lookback_days) if bar.date >= start]
```

The stated justification (`market_phase.py:210-215`, and verbatim in the dev handoff, "the number of
TRADING days within any N CALENDAR days can never exceed N") is correct but is applied to the wrong
range. The filter admits `[start, d]` **inclusive**, which is `lookback_days + 1` calendar days and can
therefore hold up to `lookback_days + 1` bars — while the fetch supplies at most `lookback_days`. The
oldest qualifying bar, dated exactly `start`, is silently dropped.

Verified two ways, both by execution, not reading:

- Direct accessor comparison on a calendar-dense synthetic series (40 bars, one per calendar day):
  `lookback_days=30` → untreated 31 bars, treated 30 bars, dropped `2024-01-10`;
  `lookback_days=20` → 21 vs 20. (`lookback_days` 50 and 365 over the same 40-bar series: identical.)
- The TC-3 comparison the iteration did not write — treated `compute_market_phase` vs the untreated
  (`bars_asof`) computation, on the *exact* fixture and `lookback_days = 30` that the shipped test
  `test_severity_reading_benchmark_window_ignores_bars_older_than_lookback_bound` uses:

  | field | untreated | treated |
  |---|---|---|
  | `severity` | 50.27 | 49.73 |
  | `drawdown_pct` | -9.25 | -8.97 |
  | `phase` | **Correction** | **Pullback** |

  A Data Contract value (the displayed market phase) changes. This is the AG-3 hazard class.

**Not reachable at the committed config — measured, not assumed.** Against the live DB
(`apps/backend/data/trendora.db`, SPY 5,391 bars 2005-02-25 → 2026-08-03) the maximum number of bars in
any `[d-365, d]` span is **255** against a 365-bar fetch, and in any `[d-50, d]` span is **37** against a
50-bar fetch (`config.yaml:1062 lookback_days: 365`, `:1077 recovery_trailing_ma_days: 50`). Both windows
carry >100 and >13 bars of slack respectively, and the `(symbol, date)` unique constraint plus
trading-day-only seed data means density can never approach 1 bar/calendar-day for SPY. So this is a
latent correctness hazard resting on an unstated, unasserted and untested data-density assumption — not a
live defect today.

Fix for iter-54 (one character each, plus a real TC-3 test): fetch `mp.lookback_days + 1` /
`mp.recovery_trailing_ma_days + 1`, which makes the count window a provable superset of the calendar
filter for every possible data density.

**B2 — GAP (filed for iter-54): the `coverage_membership_timeline` fault-injection site is not the phase it names, and cannot isolate that phase in a live drill.**

`apps/backend/app/engine/universe_resolver.py:233` places
`data_manager._fault_inject_memory_error("coverage_membership_timeline")` inside
`resolve_with_reasons`'s per-symbol loop. That function is a shared membership-resolution seam with at
least four callers (`data_manager.py:390`, `:640`, `:656`, and `universe_resolver.py:267` →
`scoring.score_stocks:282`). `_FAULT_INJECT_SITES`' own contract comment (`data_manager.py:3248-3250`)
says each site "is the exact per-item boundary whose `except MemoryError` handler J-07's acceptance
names" — that is not true here.

Confirmed from the live log, not inferred: `logs/backend.log:227201-227280` (UT-11's drill) shows every
injected `coverage_membership_timeline` MemoryError firing through
`scoring.score_stocks → resolve_members → resolve_with_reasons` inside the **per-date backfill compute**,
aborting the job before the finalize tail is ever reached — `snapshots_created: 0`,
`aggregates_refreshed` never contains `coverage`/`membership_timeline`/`market_phase`
(`data_provider_runs` id 342, read directly from the DB). The browser-QA lane disclosed this honestly
(UT-11: *"arming it made every requested date fail, not just a 'finalize tail' sub-step"*). The
new **unit** test reaches the intended handler by calling `_refresh_ingest_aggregates` directly, so TC-5
is satisfied at unit level — but no live drill can use this site to exercise
`coverage_membership_timeline_refresh`'s new handler.

**B3 — GAP (filed for iter-54): the identical unbounded full-history read survives untreated in a sibling per-run loop that serves a live endpoint.**

`apps/backend/app/engine/market_phase.py:1168` — `_benchmark_close_on_or_before` is still
`closes(bars_asof(session, bench, d))` then `series[-1]`: the exact defect shape this iteration proved
dominant in `_latest_vix_on_or_before` (65 stalls / 3.34s in one call). It is called once per stored run
(`:1203`, ~2,900 on the live basis) inside `compute_retrospective`'s own `bar_cache` loop, which serves
`/api/market-phase/retrospective` at request time. Out of this iteration's named scope (the spec bounded
it to two finalize-tail phases), but it is a request-time path in exactly the failure class this
iteration targets, and `close_on` — already imported into this module by this iteration — is a
drop-in fix.

**B4 — OBSERVATION: `_fault_inject_memory_error` now runs inside two hot loops, contradicting its own documented cost.**

Its docstring and contract block (`data_manager.py:3242`) state "the env var is read once per warm
call". After this iteration it is called once per candidate symbol per date in
`resolve_with_reasons` (548 symbols on the live pool) and once per stored run in `_severity_reading`
(~2,900 per `compute_market_phase`). Each call is a frozenset test plus an `os.environ.get`. No
observable impact — the drill measured both treated phases *faster* — but the contract text is now
inaccurate for a latency-critical iteration.

### Frontend Findings

None. `Frontend Present: no`; zero frontend files in `changed_files`; the browser lane observed existing
surfaces only and found them intact (UT-08 severity breakdown reconstructs to the displayed score
29.35≈29.36; UT-09 universe diagnostic 539 admitted + 9 excluded = 548 candidate pool — both
internally consistent, an AG-3 spot-check that passes).

### Test Findings

**T1 — IMPORTANT (gap — filed for iter-54): TC-3 is not satisfied for `market_phase`; the test shape chosen cannot detect the defect B1 documents.**

TC-3 requires "a new unit test runs the treated function against the same fixture inputs **as the
untreated computation**, then the two outputs are asserted equal". All three new market-phase tests
(`apps/backend/tests/test_market_phase.py:262`, `:308`, `:330`) instead compare **treated vs treated** —
a bare fixture against the same fixture padded with an older, differently-priced block — which proves
only that the fetch is not too *wide*. Nothing asserts it is not too *narrow*. Written as TC-3
specifies, at the very `lookback_days = 30` the shipped test itself sets, the assertion **fails** (B1's
table). The reviewer nonetheless recorded `definition_of_done: complete` and QA recorded "TC-3 ✅ PASS".

The universe-resolver half is done correctly and is worth naming as the contrast:
`test_resolve_with_reasons_adv_window_boundary_exact_short_and_long_history`
(`test_universe_resolver.py:404`) compares the bounded-fetch `resolve_with_reasons` against
`resolve_candidate(full_bars, …)` — the unchanged pure oracle — across a 6-value boundary sweep. That is
a genuine treated-vs-untreated proof, and I confirmed by code trace that this half really is
byte-identical: `resolve_candidate` reads only `bars[-1]` (staleness/price) and `_adv_dollar`'s
`bars[-adv_window_days:]`, so a COUNT window sized to `adv_window_days` is exact — a count bound feeding
a count consumer, with none of B1's count-vs-calendar mismatch. `adv_window_days` is validated positive
(`app/config.py:63-65`), so the `max(1, …)` guard is defensive only.

**T2 — GAP: an existing assertion was deleted undisclosed.**

`apps/backend/tests/test_universe_resolver.py:335` — `test_resolve_empty_db_is_honest_empty` lost
`assert out["excluded_counts"][REASON_BELOW_HISTORY] == 2`. The dev handoff lists only additions ("4 new
tests") and never mentions the deletion. I re-ran the deleted assertion independently against the same
fixture: `excluded_counts == {'below_history': 2, 'stale_series': 0, 'below_price': 0, 'below_adv': 0}`
→ **it still passes**. So this is a coverage regression and a handoff-honesty lapse, not an assertion
deleted to go green. Confirms the reviewer's MINOR issue and its `standards.test_quality: fail`.

**T3 — IMPORTANT: the QA report's TC-6 PASS cites evidence that does not show J-04 and that did not yet exist when QA wrote it; and QA's `PASS` silently overrides the browser lane's `BLOCKED`.**

`reports/qa/goal-ops-hardening-iter-53-qa.md:239` records "TC-6: J-04 evidence capture
(badge/banner/logfile) ✅ PASS | Regression replay screenshots in
`reports/qa/goal-ops-hardening-iter-53-evidence/`", and `:157-163` enumerates those screenshots as
`J-01-verify.png`, `J-03-verify.png`, `J-08-verify.png`, `J-09-verify.png` — none of which is J-04
evidence. Timestamps make the problem concrete: the QA report was written at **08:38:42**, whereas the
actual J-04 evidence is `UT-06-result.png` **08:52:57**, `UT-07-result.png` **09:09:29**,
`UT-05-result.png` **09:22:28**, and the J-05/J-07 health evidence is `UT-03-result.png` **09:15:10**.
QA asserted the item PASS against artifacts that did not exist for another 45 minutes. Separately,
`reports/phase-goal-ops-hardening-iter-53-ui-test-results.md:9` carries
**"Browser QA Verdict: BLOCKED"** with three target journeys listed as missing; the QA report's own
verdict line is `PASS` and never mentions the contradiction. This is the rubric §5/§7 evidence floor,
breached in the artifact whose whole job is to hold it.

**Mitigation, verified by reading the later artifacts myself:** the underlying DoD item *is* genuinely
satisfied. UT-05 captures `data-state="initializing"` + "Initializing… history 89/89" with first HTTP
200 at +1.29s; UT-06 captures `data-state="unavailable"` / `data-verdict="NO-GO"` after `kill -9` plus
`logs/backend.log` growing 28 lines with zero shutdown lines; UT-07 captures the interrupted-job row in
muted-neutral styling alongside a genuinely running job. TC-6 (a), (b) and (c) are all met — by evidence
QA did not cite.

**T4 — GAP (filed for iter-54): the "8-journey lane" is 4 deterministic replays; three target journeys have no golden row, and J-05's golden exists but was not run.**

`reports/phase-goal-ops-hardening-iter-53-regression-replay-results.md` shows 4/4 (J-01, J-03, J-08,
J-09). The merged file's "Missing Target Journeys" section names `UT-J-04`, `UT-J-05`, `UT-J-07` as
having "no test case executed by any lane" — which is why its verdict is BLOCKED. J-04 and J-07 have no
golden script at all (`runs/goal-session-ops-hardening/journey-scripts/` holds only J-01, J-03, J-05,
J-06, J-08, J-09; no file in it was written this iteration — newest mtime 2026-08-06), and
`runs/goal-session-ops-hardening/state/golden-gaps` (whose committed content was `J-04`) is deleted in
the working tree. **J-05's golden does exist and was not replayed**, despite J-05 being a target
journey — a free deterministic row that was left on the table.

The half of TC-7 that is a hard gate does hold, and I verified it independently rather than accepting
QA's unevidenced claim: newest `apps/backend/**` mtime **2026-08-08 07:05:37**
(`tests/test_data_manager.py`), earliest lane artifact **08:29:30** — every lane result is strictly
after the frozen tree.

**T5 — GAP: ~40 `loaded_engine`-dependent tests in `test_market_phase.py` were never run by any stage.**

The dev ran the 30 fast tests plus the 3 new ones; the reviewer ran 45; QA ran neither file. All three
disclosed this honestly (dev handoff "Known Issues", QA note at `:75`). It is the one place a real,
trading-day-density regression in `_severity_reading` would have surfaced against seed data — it would
not have fired (B1's measured margin), but "no regressions in the existing backend test suite"
(DoD item 8) is therefore evidenced only for the fast subset.

---

## 3. Domain Assessment

The core engineering judgement in this iteration is **good, and better than the spec asked for**. The
spec licensed applying iter-52's `_cooperative_sorted`/`_cyclic_gc_paused` pattern by analogy; the
developer instead ran a real GIL-stall profile (worker thread + tight-loop probe capturing
`sys._current_frames()` at stall resolution) against a throwaway copy of the committed DB, found a
*different and simpler* defect — full-history `bars_asof` fetches feeding trailing-window consumers —
and explicitly declined to force-fit the iter-52 pattern onto it. That is exactly iter-48's lesson
executed, and the 36x drop in `market_phase_warm` (26.26s → 0.73s) is the profile validating itself.

Reusing `bars_asof_window`/`close_on` rather than writing new accessors is the right call: both are
cache-aware at the same `_BAR_CACHES.get(id(session))` seam as `bars_asof` (`prices.py:648`, `:676`),
both were proven byte-identical in iters 26/27, and neither introduces a second source of bar truth —
so the Data Contract's "single canonical computing module" property is preserved and no new producer
appears for any registered value. The `bar_count` pass-through in `resolve_candidate`
(`universe_resolver.py:107-108`) is the right shape: it keeps the *disclosed* trailing-bar count the
true history while the *fetch* shrinks, and it is guarded by a dedicated test. I traced this half end to
end and it is genuinely byte-identical.

The correctness slip is confined to one class: substituting a **count** bound for a **calendar** filter
in `market_phase`, where the two are not interchangeable, with the mismatch masked by a test written in
a shape that cannot see it. The failure mode is instructive — the reasoning in the comment is careful
and almost right, and it is the off-by-one at the interval endpoint that breaks it. That is precisely
why TC-3 mandated a treated-vs-untreated comparison rather than a self-consistency check.

Honesty across the artifacts is otherwise strong. Addendum 15 leads with the *worse* number (1,559.30s,
29.9% over vs Addendum 14's 5.1%) before explaining it, attributes the residual non-answer to a
neighbouring phase rather than folding it into "closed", and explicitly declines to claim the ≤2s
ceiling. The dev handoff volunteers that `_severity_reading`'s benchmark fix was never independently
confirmed as a live stall source. UT-11 volunteers that its own fault injection had broader blast radius
than the test's framing anticipated. That is the right instinct throughout — which makes the QA report's
mis-cited TC-6 the outlier, not the pattern.

---

## 4. Fixes Applied During This Audit

**None — deliberately.** DoD item 5 / TC-7 of this iteration's own spec binds the audit step to file
notes rather than apply code-changing fixes, so that the frozen-tree lane evidence stays valid for the
tree it measured (the failure that made iter-52 unscoreable, and that broke 6 of the last 7 rounds). All
findings above that need a code change (B1, B2, B3, T1, T4) are filed for iter-54. I verified my own
compliance: `git status --porcelain` shows no file changed by this audit; all my verification ran from
standalone scripts in `$TMPDIR`.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fix applied (TC-7 binding sequencing rule; findings filed for iter-54) |

**Verification I ran myself (not accepted from any handoff):**

| Check | Command / method | Result |
|---|---|---|
| New + targeted tests | `pytest tests/test_universe_resolver.py tests/test_data_manager_membership_cache.py` + the 2 TC-5 fault-injection tests + the 3 new market-phase tests | **41 passed in 5.41s** |
| B1 off-by-one (accessor) | standalone script, calendar-dense 40-bar series | `L=30`: 31 vs 30 bars, `2024-01-10` dropped; `L=20`: 21 vs 20 |
| B1 off-by-one (served value) | treated vs untreated `compute_market_phase`, shipped fixture, `lookback_days=30` | phase `Correction` → `Pullback`; severity 50.27 → 49.73 |
| B1 production reachability | live DB, max bars per span, SPY 5,391 bars | 255 ≤ 365 and 37 ≤ 50 → **safe with margin** |
| T2 deleted assertion | re-ran the deleted assertion against the same fixture | `below_history == 2` → still True |
| B2 site scope | `logs/backend.log:227201-227280` stack frames | fires via `score_stocks → resolve_members`, not the finalize tail |
| TC-8 / AG-10 | `git diff --stat` + `git status --porcelain` over the 5 frozen paths | both **empty** |
| AG-9 | `data_provider_runs` read directly from the DB | ids 335-342 (2026-08-08) all `provider='seed'`; newest non-seed row 2026-08-04 |
| TC-4 | job 336 `aggregates_refreshed` from the persisted row | `coverage`, `membership_timeline`, `market_phase` all present, as before |
| TC-4 (no new MemoryError) | `logs/backend.log` scan | only the deliberately injected UT-11 errors; none unexplained |
| TC-7 freeze | mtime comparison | newest `apps/backend/**` 07:05:37 < earliest lane artifact 08:29:30 |

**Definition-of-Done trace.** Items 1, 2, 3, 4, 5, 7, 8, 9 got the full trace (risk class: data
correctness, failure handling, frozen surfaces; plus the QA-vs-lane contradiction). Item 6 (J-01/J-03/
J-08/J-09 replay PASS) is mechanical and accepted on the reviewer's PASS (no issue touching it,
`spec_alignment.definition_of_done: complete`) plus the executed QA row "Regression Replay Results —
4/4 PASS" with four screenshots, which I confirmed exist with mtimes 08:32:10-08:32:26.

| # | DoD item | Verdict |
|---|---|---|
| 1 | Both phases bounded; unit test proves byte-identical output for each | **PARTIAL** — resolver half proven; market-phase half not proven and not true as stated (B1, T1) |
| 2 | Concurrent drill measures the two phases' non-answers; new addendum records it honestly | **MET** — Addendum 15, both phases 0, disclosed honestly including the worse total |
| 3 | MemoryError isolate-and-continue unchanged for both, fault-injection verified | **MET** at unit level (2 new tests + the pre-existing partial-success test); B2 caveat on live drills |
| 4 | J-04 steps 3-5 first evidence capture | **MET** by UT-05/06/07 — but not by the evidence QA cited (T3) |
| 5 | 8-journey lane dispatched LAST against a frozen tree; audit files notes, not fixes | **PARTIAL** — freeze verified; lane is 4 replays, 3 targets have no golden row (T4). Audit complied |
| 6 | J-01/J-03/J-08/J-09 replay PASS | **MET** (reviewer PASS + QA replay row, 4 screenshots) |
| 7 | No anti-goal violation (AG-8 / AG-9 / AG-10) | **MET** — all three re-verified independently |
| 8 | Unit tests pass; no regressions | **MET for what was run** (41 passed, my own run); ~40 `loaded_engine` tests never run (T5) |
| 9 | Dev handoff names both phases, profiled GIL-hold source, drill result honestly | **MET** — one inaccuracy, the byte-identity claim (B1) |

---

## 5. Recommended Next Step

**Proceed.** The iteration delivered its stated goal with measured, honestly-reported evidence, and
nothing found here breaks the product at the committed configuration.

Carry these into iter-54, in this order:

1. **B1 + T1 (do these together, first).** Change the two fetches to `mp.lookback_days + 1` and
   `mp.recovery_trailing_ma_days + 1`, then write the TC-3 test the spec actually asked for — treated
   `compute_market_phase` vs the untreated `bars_asof` computation on the same fixture, at a *small*
   `lookback_days` where the boundary is exercised. The reproduction is in §2/B1; the corrected test
   must pass at `lookback_days=30`, which today it would not. Correct the byte-identity language in
   `market_phase.py:210-215`, the dev handoff and Addendum 15 at the same time — the claim is currently
   stronger than the code earns.
2. **T3, as a process correction of record.** I did not edit the QA artifact (historical record, and
   TC-7's spirit is that this round's evidence stays as measured). Iter-54's QA stage must not write
   PASS rows for evidence that does not yet exist, and must surface — never silently override — a
   `BLOCKED` verdict from the browser lane.
3. **T4.** Author golden replay scripts for J-04 and J-07, and run J-05's existing golden. Three target
   journeys with no deterministic row is the same class of hole the iter-41/42 audits already closed
   once; `state/golden-gaps` is currently deleted in the working tree, so the next iteration's golden
   nudge has lost its input.
4. **`per_date_coverage_warm`** — the single remaining connection-level non-answer relocated there
   (Addendum 15, t+165.8s). Same profile-then-bound methodology, now proven twice. Then
   `forward_aggregates_warm` (12 of the 14 remaining >2.0s polls) and `drawdown_expectations_warm`,
   which is what the 1,200s finalize-tail budget actually needs.
5. **B3** — `_benchmark_close_on_or_before` (`market_phase.py:1168`) is a one-line `close_on`
   substitution of the exact defect this iteration proved dominant, on a request-time endpoint path.
6. **B2** — either rename the fault-injection site to what it gates (`universe_resolver`) or move the
   probe to the finalize-tail boundary it claims to name, so a live drill can isolate that phase.
7. **T5** — run `test_market_phase.py`'s `loaded_engine` tests once at reviewer/QA stage.

The two owner questions carried since iter-50 remain unanswered and still bound the ceiling: (a) may
heavy compute move to a separate process/worker boundary, and (b) is the 1,200s finalize-tail budget an
idle budget or a concurrent-load budget. Neither blocked this iteration; both will keep re-appearing
until answered.
