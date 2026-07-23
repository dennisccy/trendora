# goal-ops-hardening-iter-13 Audit Report

**Date:** 2026-07-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's own goal — bring `GET /api/indexes?full=true`'s single unparameterized default hot key
within its ≤1.5s budget by warming it at ingest — is **decisively achieved and honestly verified**: the
canonical real-Chrome control readings are 218.7 / 218.7 / 219.2 ms on `/data` and 70.5 ms on `/`
(spot-check), all ≤1500 ms with ~7× headroom on a verifiably idle host (`load1` 0.36–0.69), versus the
confirmed 2138.7–2257.7 ms pre-fix baseline. I traced every DoD item through the actual code, confirmed
byte-identity and the invalidation/honesty-gating logic, verified `forward_testing.py` is byte-unchanged
(TC-12), and confirmed the two slow test logs are real with the exact cited pass counts. No CRITICAL or
IMPORTANT defect exists in this iteration's deliverable. The gaps that remain are (a) J-04's explicit
re-verification was not produced (its boot path is provably byte-unchanged, so risk is negligible), (b) the
browser-qa OVERALL=FAIL is mechanically driven entirely by UT-07 asserting against dead/unreferenced code,
and (c) the standing owner-scoped AG-8 `MemoryError` — untouched in code here but **observed-severity-
escalated to a full 12-min availability outage** during this iteration's testing — still hard-blocks
session-level GOAL_ACHIEVED.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): `index_series_dataset_version` docstring overclaims what its stamp detects**
`apps/backend/app/engine/indexes.py:200–201` — the stamp is `max(date) + count(*)` over the configured
`index_chart.symbols` (verified at `indexes.py:206–219`), and the docstring claims it "Changes whenever a
configured index symbol gains, loses, **or has a bar altered** anywhere in its history." A `max(date)+count(*)`
stamp cannot detect an **in-place value mutation** of an existing bar (same date, same row count → identical
stamp → the cache serves the pre-mutation series). The spec (DoD #3 / TC-4) only ever required invalidation
on a **new** bar, which does work correctly (count increments → MISS → recompute; proven by
`test_index_series_cached_invalidates_after_new_bar_for_configured_symbol` and the dataset-version unit
tests). Under **AG-9 (offline-deterministic ingest — no live fetch)** an existing index-ETF bar's value is
never revised in place, so this path is not reachable in the current system. No fix applied (docstring
accuracy only; the spec'd behavior is correct and tested). Recommend tightening the docstring, or folding a
`SUM(close)`/hash term into the stamp, only if a bar-revision workflow is ever added.

**B2 — OBSERVATION (observation): commit-rollback branch returns `persisted=True` on a concurrent-writer race**
`apps/backend/app/engine/indexes.py:277–281` — on a MISS the wrapper inserts the row, then
`session.commit()`; if the commit raises (a concurrent writer already inserted the same
`(range_key, full, dataset_version)` key), it `rollback()`s and still `return payload, True`. The finalize
hook (`data_manager.py:3277–3279`) then appends `"index_series"` even though *this* call's INSERT was rolled
back. The DoD-#4/TC-5 honesty gate says report the category only when "the warm step actually persisted a row
this run." This is substantively honest (a row for the current stamp *does* exist after the race — the racer
wrote it — so the cache is genuinely fresh for the run's dataset version) and it exactly matches the
established sibling convention (`market_phase_cached`, `forward_aggregates_cached`, `event_study_cached` all
carry the identical commit/rollback/"byte-identical payload" pattern — verified). In the single-writer
offline ingest model this race is essentially unreachable. No fix applied (OBSERVATION; consistent with the
whole cache family).

### Frontend Findings

**F1 — GAP (observation): browser-qa OVERALL=FAIL is driven solely by UT-07 asserting against dead code**
`reports/phase-goal-ops-hardening-iter-13-ui-test-results.llm.md:182` marks UT-07 (a P1 gate item) FAIL
because `document.querySelectorAll('[aria-label="Range preset"]')` returns 0 matches. I independently
confirmed the owning component `apps/frontend/components/major-indexes-card.tsx:34` (`MajorIndexesCard`) is
**never imported anywhere in `apps/frontend/`** (`grep` returned only its own definition line) — it is dead,
unreachable code, superseded by `PhaseCrossViewCard` in iter-6. Zero frontend files changed this iteration
(verified). The acceptance UT-07 actually cares about — an explicit non-default range still uses the
unchanged, uncached path — is independently proven by real-browser `fetch()` (200, 661 ms, 10 series) and by
the tight unit test `test_api_indexes_non_hot_key_bypasses_cache_and_stays_byte_identical`. This FAIL is a
**stale test-plan defect, not a product regression**. Retiring UT-07 / deleting the dead component is a
test-plan + UI-backlog item explicitly outside a product iteration's remit (goal.md OUT OF SCOPE: never patch
harness/test-plan artifacts from a product iteration; ux-regression independently recommends the same at
`…-ux-regression.md:127–129`). No fix applied.

### Test Findings

**T1 — GAP (observation): J-04 was not re-verified this iteration; the deterministic replay covered only 3 of the 4 required journeys**
`reports/phase-goal-ops-hardening-iter-13-regression-replay-results.md:19–21` records UT-J-01, UT-J-03,
UT-J-05 (all PASS, "3/3 journeys passed") — **J-04 ("Non-blocking boot with visible status") is absent.**
DoD #7 and TC-8 name all four of J-01/J-03/J-04/J-05. I considered marking this IMPORTANT (a spec'd
verification not produced), but the boot surface J-04 exercises is **provably byte-unchanged this iteration**:
`main.py`, `app/api/health.py`, `app/engine/readiness.py`, and `app/engine/warmup.py` are all absent from the
diff (verified via `git status`). The only boot-path touch is `create_all` materializing one trivial new
`index_series_cache` table; the new warm step lives in the ingest finalize hook, which never runs during
boot. The spec's own OUT OF SCOPE downgrades boot to "spot-check only … unchanged and fresh since iter-11
(1.364 s boot)." Given the journey's entire surface is untouched, the missed re-verification is a
coverage/documentation gap with negligible functional risk, not a broken flow — hence GAP. Recommend the next
browser-qa pass include a J-04 boot spot-check to close the DoD-#7 wording literally. No fix applied (a boot
journey requires a service restart, which agents cannot perform this session per the plan).

---

## 3. Domain Assessment

The core domain logic is correct, minimal, and idiomatic to this codebase — this is a well-executed cache.

- **Byte-identity (AG-3).** The wrapper is a pure serving/persistence layer over the **unchanged**
  `compute_index_series` (its body/signature/other call sites are untouched — verified in the diff and via
  `git status` on `app/mcp/*`). Every value `compute_index_series` returns is JSON-native (dates are
  `.isoformat()`'d, `pct` is a `round(...)` float — `indexes.py:155–178`), so the `json.dumps`/`json.loads`
  round-trip in the cache path yields an equal dict. `payload == expected` full-dict assertions cover this at
  three layers (`test_indexes.py`, `test_api_indexes.py`, plus the developer's live out-of-process check).
- **The as-of correctness trap is correctly avoided.** For the `range_key="all"` hot key, `start` is `None`
  and `full=True` reads `bars_through_latest` (both independent of the resolved as-of — `indexes.py:143–147,
  148`), so the only as-of-dependent field is the echoed `asof_date`, which the HIT path **re-derives** via
  `resolve_as_of_date(session, None, cfg)` rather than trusting the stored value (`indexes.py:246–249`). This
  exactly matches what a fresh compute would echo (`scanner.py:314–315`), and
  `test_index_series_cached_hit_re_derives_current_asof_not_stale` proves a new `ScannerRun` shifts the echoed
  as-of on a HIT while the series is served verbatim. Genuinely thoughtful.
- **Narrow invalidation stamp.** Scoping the stamp to only the index symbols' bars (not the broad
  `research._dataset_version`) mirrors the `_membership_dataset_version` precedent and avoids needless
  invalidation on unrelated ingest — proven by the two dataset-version unit tests (configured-symbol bar bumps
  it; an unrelated symbol's bar does not).
- **Honest gating + failure isolation.** `aggregates_refreshed` appends `"index_series"` only on a real
  persist (`persisted_this_call`), a *stricter* honesty gate than the siblings require, and the live backfill
  confirmed it is honestly **omitted** on a HIT. The `MemoryError` branch is caught distinctly, stops
  immediately, calls `_release_process_memory()`, and never flips the job status — the iter-8 convention,
  exercised by `test_finalize_hook_index_series_memory_error_isolated_and_not_reported` (asserts the other
  five categories still refresh and the hook never raises). The mid-hook `session.commit()` is the same
  established pattern every sibling cache already uses (verified across `market_phase.py`/`forward_testing.py`/
  `research.py`), not a new transaction hazard.
- **Routing.** The hot-key predicate (`full and as_of is None and (range is None or range ==
  default_range)`, `api/indexes.py:49`) is exact; every other combination calls the unchanged
  `compute_index_series` and never touches the cache (proven byte-identical + zero-row-write by
  `test_api_indexes_non_hot_key_bypasses_cache_and_stays_byte_identical`).

**Test quality** is high: assertions are tight (full `==` dict equality, recompute-call counting to prove a
HIT never recomputes, exact row-count checks, honest-omission checks). Verified: `forward_testing.py`
byte-unchanged (TC-12), no `apps/frontend/` change, and both slow logs real (`15 passed in 4844.71s`,
`30 passed in 130.26s`).

**Anti-goal assessment (session-level, recorded accurately per the operator note).** DoD #8 requires the
critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load `MemoryError`
(`forward_testing.py:826`) be "neither newly introduced nor worsened (its code path untouched)." **At the
code level this holds** — TC-12 confirms the file is byte-unchanged. However, its **observed operational
severity escalated during this iteration's own testing**: the single bounded backfill run for TC-4 tripped it
again, and under concurrent browser-qa load (4 replay backfills + a diagnostic read) it wedged the **entire
backend into a ~12-minute futex deadlock** (all threads parked, `/api/health` unresponsive) that required an
operator hard-restart. AG-8 is therefore now demonstrably capable of a **full availability outage**, not just
a silent internal abort — this is the dominant standing session risk and, with `HOST_GUARD_REQUIRE_MARKERS`
and the `demo.sh --session-live` walkthrough, one of the three owner decisions that continue to hard-block
GOAL_ACHIEVED regardless of J-06's outcome (exactly as the spec's NOTES anticipate). It is out of scope to fix
here and was correctly not touched. AG-10 host-guard confinement was honored for every test run.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP or OBSERVATION level; fixing them would be scope creep. No CRITICAL or IMPORTANT
defect was found in this iteration's deliverable, so no source file was modified by this audit.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (no CRITICAL/IMPORTANT findings). |

---

## 5. Recommended Next Step

**Proceed.** J-06's last agent-owned gap is closed on the number, not merely in code: the hot key lands
≤1500 ms with ~7× headroom across three fresh-navigation real-Chrome `/data` loads plus the `/` spot-check on
an idle host. With J-01/J-03/J-05 replayed green and J-04's boot surface byte-unchanged, all five Must-have
journeys are materially passing.

The next decomposer pass should write the **"all journeys passing, owner decisions outstanding" holding
spec** the spec's own NOTES call for — not manufacture new journey scope — because GOAL_ACHIEVED remains
hard-blocked by three owner decisions, now led in urgency by the **AG-8 `MemoryError`, which this iteration
demonstrated can take the whole backend down for 12+ minutes**. Two small, non-blocking hygiene items worth a
backlog note: (1) add a J-04 boot spot-check to the next browser-qa pass to satisfy DoD #7 literally; (2)
retire UT-07 / decide the fate of the dead `major-indexes-card.tsx` so future browser-qa runs stop failing
their OVERALL verdict against unreachable code.
