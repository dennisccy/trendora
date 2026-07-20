# goal-ops-hardening-iter-3 Audit Report

**Date:** 2026-07-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's three stated deliverables — B1 (fetch/expand now refresh `coverage_snapshot`), B2
(stale-`dataset_version` rows reclaimed in one bounded DELETE), and J-05's step-4 live health/memory
measurement — are all correctly implemented, independently verified (I re-ran the 6 new tests myself: all
pass; I traced the code and confirmed the byte-identity, zero-compute, and one-DELETE contracts hold), and
carry zero product-code scope creep (only the two intended files changed). B1 was this session's declared
#1 blocker to GOAL_ACHIEVED and it is genuinely closed. However, this iteration's own thorough browser/
heavy-job testing (the first this session to drive a real heavy job and a plain fetch through the browser)
surfaced two **serious but pre-existing, out-of-scope** defects in untouched shared components (a false
"Backend unavailable"/NO-GO state on an ordinary fetch; a frozen job-progress heartbeat during the finalize
loop), plus a few evidence gaps. None of these stems from this iteration's diff, so none compromises its
scoped goal — but they keep the J-05 journey from a clean browser pass and are documented below as the
mandatory next-iteration priorities.

---

## 2. Findings

### Backend Findings

**B1-verify — PASS (no finding): the B1 fetch/expand coverage-freshness fix is correct.**
`_run_job` (`apps/backend/app/engine/data_manager.py:3793-3813`) adds a new `elif` that fires for a
successful (`ok`/`partial`) pure `fetch`/`expand`. The `elif` (not a second `if`/bare `or`) structurally
excludes `"both"` — which is in BOTH `_FETCH_KINDS` and `_BACKFILL_KINDS` — so `"both"` still runs the rich
path exactly once (verified against the kind-set definitions at `:94-107`). The branch calls
`refresh_coverage_snapshot` (the SAME canonical `_compute_coverage_uncached` derivation, `:1037`) gated by
the new cheap `_coverage_snapshot_is_current` (`:1060-1081`). The gate hinges on `_membership_dataset_version`
(`app/engine/research.py:1550-1598`), which folds in `count(daily_prices)` + `max(daily_prices.date)` — so
ANY landed bar changes the stamp, no row exists for the new key, and the refresh fires; a zero-work fetch
leaves the stamp unchanged so the gate short-circuits before any compute. `test_fetch_that_lands_new_bar_
refreshes_coverage_snapshot` proves the end-to-end result with a REAL `run_data_job` fetch:
`assert new_version != pre_version`, `assert stored == fresh`, and `assert served == fresh`
(`coverage_from_storage(..., as_of=None)` — the exact path `GET /api/data`'s default view reads). The
false-all-zero regression is gone.

**B2-verify — PASS (no finding): the B2 stale-row prune is correct and safe for the shared rich path.**
`_upsert_coverage_snapshot` (`:1001`) now issues one bulk `delete(CoverageSnapshot).where(dataset_version
!= :current)` before the upsert (the `delete` construct is imported at `:46` — verified). Because the
serving path (`coverage_from_storage`, `:1116`) always resolves the CURRENT `_membership_dataset_version`,
every row under any other version is by definition unservable/dead, so reclaiming them is always safe. The
delete only targets `!= current`, so sibling current-version rows written by the rich path's per-date loop
(`_persist_per_date_coverage_snapshots`, `:3027-3029`) survive — the version is stable across that read-only
loop. `test_stale_dataset_version_rows_pruned_via_one_bulk_delete` asserts exactly ONE DELETE statement runs
(SQL-event-listener) and only the new row remains. The full `test_data_manager.py` (109 passed, incl. the
rich-path finalize-hook tests) corroborates no rich-path regression.

**B3 — GAP (gap, pre-existing, OUT OF SCOPE): an ordinary fetch can drive the whole app into a false
"Backend unavailable" / "NO-GO — do not rely on today's board" state, with no in-app recovery.**
Surfaced by browser QA (`reports/phase-goal-ops-hardening-iter-3-ui-test-results.md`, Additional Finding;
`ux-regression` High finding). A bare "Fetch EOD prices" that lands one `^VIX` bar for a date beyond SPY's
latest snapshot flips the global `HealthBadge`/`PreflightBanner` to a state visually identical to a real
crash, while the backend is fully healthy; only "Remove imported data" (a deletion control) clears it.
**Root cause (I traced it): `app/engine/readiness.py:129`** — `latest_servable = latest_run is not None and
latest_run >= latest_data`. When a fetched bar advances `max(DailyPrice.date)` past `max(ScannerRun.asof_
date)`, servability flips to `unavailable` → NO-GO. This reads `DailyPrice`/`ScannerRun` directly, **not**
`coverage_snapshot`, and **`readiness.py` was untouched this iteration** (verified: empty `git diff`). So
this is pre-existing behavior fully orthogonal to the B1/B2 diff — it would fire identically without this
iteration. It is severe (it directly undermines the user-facing value of the very fetch action this
iteration hardens, and arguably the state is *technically* honest — the board genuinely hasn't scored the
new date — but it is mis-presented as an outage with no guided remedy). It is explicitly OUT OF SCOPE
(the spec forbids touching readiness/boot mechanics and J-04 fields; fixing it needs a UX/design decision).
Documented, not fixed. **This is the #1 follow-up.**

### Frontend Findings

**F1 — GAP (gap, pre-existing, OUT OF SCOPE): job-progress heartbeat freezes → false "· possibly stalled"
for most of a heavy job's duration.** UT-06 FAIL (reproduced twice): the `JobProgressPanel` heartbeat froze
for ~83-84% of a ~320s job and the UI live-rendered "updated 33s ago · possibly stalled" while the job was
healthy and `status` was still `"running"`. Root cause: `_refresh_ingest_aggregates`'s sequential per-date
loop (the iter-2-shipped finalize hook, `apps/backend/app/engine/data_manager.py:3034+`) emits zero `tick()`
calls during its ~729s run (corroborated by `reports/perf-budgets.md` Item L's stage table). Pre-existing
and untouched by this iteration's diff; undermines J-04's "visible status stays accurate" promise. The
global `HealthBadge` itself stayed "Ready" throughout (UT-06's own confirmation), so J-05 step-4's actual
`/api/health` acceptance is not implicated by this. Documented, not fixed (out of scope).

**F2 — GAP (gap): B1's user-facing legibility.** For an ordinary top-up fetch on the full DB, only the
"Price history" end-date tile moves (and persists through reload — the live proof B1 fires); Symbols/
Trading-days/Snapshot-dates do not move by design (Trading-days keyed to SPY's own bar dates; Symbols only
moves for a wholly-new symbol; Snapshot-dates never moves for a fetch). This is a legibility gap, not a
broken feature — the fix works. Honestly disclosed in `user-visible-changes.md` / ux-regression. Note only.

### Test Findings

**T1 — IMPORTANT (gap, process/honesty): the QA report overstates the browser verification and omits the
browser-qa FAIL verdict.** `reports/qa/goal-ops-hardening-iter-3-qa.md` marks TC-11 **PASS** and reports a
clean **12/12**, with "Browser UI verification confirms the B1 fix works correctly" — but its TC-11 evidence
is a *static* `/data` load (observing pre-existing populated coverage 540/591/5380/762), NOT the fetch→
reload cycle TC-11 specifies. The browser-qa-agent that DID run the fetch cycle reported **Browser QA
Verdict: FAIL** (`reports/phase-goal-ops-hardening-iter-3-ui-test-results.md`: UT-02 FAIL, UT-06 FAIL,
UT-04 SKIP). The QA report neither surfaces that FAIL nor reconciles it. The underlying conclusion (B1
works) is nonetheless correct — I independently verified it via the unit suite and by root-causing UT-02's
"failure" to a misaligned tile-increase expectation the mechanism actually satisfies — but the QA artifact
reached the right answer on thinner evidence than it claims and buried a contradicting signal. This is
exactly the class of gap the audit exists to catch. Cannot be surgically "fixed" by me (the browser run is
the browser-qa-agent's; the conclusion is already correct); recorded so the evaluator weighs the real
browser result, not the QA report's clean-pass framing.

**T2 — GAP (gap): TC-8's literal "within 1s" is not 100% met, and UT-04 (J-05 step-3 cold-boot live check)
was skipped.** Item L records 50/1,725 health polls (2.9%) at 1.00–3.29s during the parallel-backfill
window (zero non-200, zero timeout, zero hang; the ~729s finalize loop showed zero degradation). goal.md's
actual J-05 step-4 acceptance is the qualitative "stays responsive throughout" (not a numeric bound), which
the honest data plausibly satisfies; the "within 1s" is a stricter test-plan interpretation. Not
attributable to this diff (a `rebuild` routes through the untouched `_refresh_ingest_aggregates`). Separately,
UT-04 (live fresh-boot all-zero regression, J-05 step 3) was SKIPPED for lack of a pristine DB — the
cold-boot guarantee rests on unit tests this round (TC-5 + `test_api_data.py` 48 passed), not a live click.
Both honestly disclosed. Note only.

---

## 3. Domain Assessment

The core domain logic is sound and, notably, the diff is genuinely surgical — the entire fix is a widening
of *when* an already-canonical value (the coverage payload) is refreshed, not a new computation or a new
serving endpoint. Single-producer/single-serving-endpoint (the coherence-auditor's data-contract concern)
is preserved: `coverage_snapshot` still has exactly one producer (the ingest finalize hook) and one reader
(`GET /api/data`); `blueprint.md`'s Coverage payload row is correctly retagged `[TARGET, iter-3 building]`
with an accurate description, and the `aggregates_refreshed` nullability contract is explicitly preserved
(`_breakdown_computed = _is_backfill_like and prog.calendar_days > 0` at `:3377` keeps the field null for
fetch/expand; the new elif deliberately does not set it — confirmed live by UT-09). The honesty conventions
hold throughout: the zero-work gate is proven by a real call-count assertion (TC-2), byte-identity by
`stored == fresh` on a real job (TC-1/TC-3/TC-6), no-network by a real socket monitor (TC-7), and the
memory/health measurement is reported precisely (the 2.9% slow-poll window disclosed rather than
force-rounded). The one substantive domain observation is not about the diff at all: the fetch-then-
readiness interaction (B3) means the *product* story "a fetch keeps /data honest" is undercut by a
pre-existing servability-gap presentation the app can't gracefully recover from — a real product debt the
diff is correct to leave untouched but that the session must retire next.

---

## 4. Fixes Applied During This Audit

None. The iteration's own diff has no defect to fix — it is correct, tested, and scope-clean (I re-ran the
6 new tests: `6 passed`). Every finding above is either pre-existing and in explicitly OUT-OF-SCOPE modules
(`app/engine/readiness.py` for B3, the untouched `_refresh_ingest_aggregates` per-date loop for F1), a
legibility/evidence gap (F2, T2), or a process gap in a sibling artifact whose conclusion is already correct
(T1). Fixing B3/F1 would mean editing modules the spec forbids touching and would require a UX/design
decision (how the servability-gap state should be presented and recovered) — that is scope creep and a
human/product call, not an audit fix. Per the auditor rules, they are documented as gaps, not patched.

---

## 5. Recommended Next Step

Proceed — the iteration's scoped goal (B1/B2 + J-05 step-4 measurement) is achieved and independently
verified; B1, the session's declared top blocker, is closed. But **do not treat J-05 as cleanly
browser-passing yet**: hand the goal-evaluator the real browser/ux verdicts (FAIL) alongside this
root-cause analysis so it scores J-05 on substance, and prioritize a focused follow-up iteration for the
two pre-existing defects this round exposed — **(1, highest) the false "Backend unavailable"/NO-GO state an
ordinary fetch triggers via `readiness.py:129`'s servability gap, with an honest "new data ingested — run a
backfill to score it" presentation and an in-app recovery path; (2) a `tick()` heartbeat during
`_refresh_ingest_aggregates`'s per-date finalize loop** so a healthy heavy job never renders "possibly
stalled." Both are cross-cutting and were correctly deferred here (rule 5: never bundle a second risky
change), but they now gate the user-facing credibility of the ingest/readiness surface. J-06 (the
measurement capstone) remains the queued Must-have journey once J-05's browser story is clean.
