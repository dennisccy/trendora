# Phase goal-ops-hardening-iter-5 — UX Regression Review

**Date:** 2026-07-20

**Verdict:** UX-REGRESSION-FAIL

This iteration (J-06 capstone, "Pages load only what they need") is a measurement + code-audit pass
with zero frontend diff and no new navigable capability, so the classic "hidden/undiscoverable
capability" failure modes this review normally hunts for do not apply here — that axis is clean. The
FAIL verdict is driven entirely by Step 2 (regression risk): the most-recently-produced artifact in
this iteration's own pipeline (`reports/phase-goal-ops-hardening-iter-5-regression-replay-results.md`,
timestamped after the QA report) shows the required-still-passing P1 journey **J-01 failed its
deterministic golden-script replay**, with no LLM-fallback adjudication recorded and two of the four
required-still-passing journeys (J-04, J-05) never replayed at all this cycle. This directly matches the
rubric's FAIL trigger: "clear regression in a prior user journey."

---

## New Capability Discoverability

Per `reports/phase-goal-ops-hardening-iter-5-user-visible-changes.md` and the plan's own "UI Evolution"
section, this iteration shipped **no new user-facing capability** (the contingent loading-indicator
fix was never triggered — no page was over budget on the final clean measurement pass) and **zero
frontend files changed** (`git diff --stat HEAD -- apps/frontend/` is empty, confirmed directly).

The one visible change is additive text inside an already-existing, already-discoverable element:

| Change | Where | Navigation path | Assessment |
|---|---|---|---|
| `BackfillBreakdown`'s "Refreshed: ..." line gains a possible new word, "forward aggregates" | `/data`, three render sites (live Job progress panel, cross-session `LastRunSummary` card, Run History table row) | Already 1 click from home (Data Manager nav link) — this is a pre-existing component, not new UI | Not hidden, not undiscoverable — it rides an existing generic renderer that already displays whatever list the backend sends. No navigation change needed or made. |

No hidden capability, no undiscoverable capability, and no label confusion found. This axis is clean.

---

## Regression Risk

### Shared-component touch: `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py`)

This is the exact function iter-4 patched (B3/F1: `prog.tick()` heartbeat fix) to make J-04
("Non-blocking boot with visible status") and J-05 ("Aggregates are precomputed at ingest, never on the
fly") pass. Iter-5 adds a new unconditional block inside this same function (lines ~3106-3130) that warms
`ForwardAggregateCache` for all 5 configured horizons on every successful ingest. Read directly: the
developer did correctly reuse the F1 heartbeat idiom (`prog.tick()` once per horizon before each
potentially-slow compute, explicitly commented as intentional), which meaningfully lowers — but does not
eliminate — risk to J-04's heartbeat-freshness assertion. **Risk: Medium** (mitigated by the tick() reuse,
but this is still new code in the exact function two prior journeys depend on, executing a change that
adds real wall-clock time to every backfill/rebuild/fetch+backfill job).

### Materially longer ingest jobs

The reviewer's own note (`reports/reviews/goal-ops-hardening-iter-5-review.md`) states the unconditional
forward-aggregates warm step adds "~35-40s to every backfill" and that `perf-budgets.md`'s own
backfill-timing rows go from ~45s to ~82-104s across passes. This changes the timing profile of the exact
workflow J-01's and J-04's golden scripts exercise (submit a backfill job, then check its resulting state).

### Confirmed failure: J-01 regression replay

`reports/phase-goal-ops-hardening-iter-5-regression-replay-results.md` — produced by `demo_runner.py`
(deterministic replay), timestamped **after** both the review report and the QA report, i.e. the most
current evidence available for this iteration — records:

| Journey | Priority | Verdict | Failure detail |
|---|---|---|---|
| J-01 "Backfill honors the requested range and explains zero-work" | P1 | **FAIL** | step 06 expected "2026-05-15" did not appear |
| J-03 "No per-run range cap" | P1 | PASS | — |

J-01's golden script (`runs/goal-session-ops-hardening/journey-scripts/J-01.json`) submits a backfill for
`2026-05-02`→`2026-05-03`, then navigates to `/scanner-runs` expecting the literal text "2026-05-15" to be
present (a historical run seeded by an earlier iteration, used as a proxy check that run history is
intact). The evidence screenshot (`reports/qa/goal-ops-hardening-iter-5-evidence/J-01-verify.png`) shows
the Scanner Runs table's visible rows spanning only `2026-07-10` through `2026-07-17` — i.e. the run
history has grown substantially since J-01's script was authored (iter-1).

This iteration's own dev handoff states it ran **four independent real backfill jobs** against the same
dev database as part of `scripts/measure-perf.sh`'s bounded-backfill measurement sub-step — directly
adding rows to the same `ScannerRun` history table (`/api/runs`, the `/scanner-runs` page) that J-01's
assertion depends on, and that this iteration's own TC-09 explicitly measured. Whether the root cause is
this iteration's own backfills pushing the target row further down an unpaginated-but-growing list, a
pre-existing brittleness in a golden script written against iter-1-era history depth, or something else,
is not resolved anywhere in the artifacts read for this review — **and that is itself the flag**: nothing
in the pipeline investigated or explained this failure before it reached this review step.

**Compounding factors:**
- Per the plan's own regression-replay commitment ("deterministic golden script + LLM fallback on a
  miss"), a miss on J-01 should trigger an LLM-fallback confirmation. No such fallback result exists
  anywhere in the reports/runs directories for this iteration — the miss was never adjudicated.
- Only J-01 and J-03 were replayed. **J-04 and J-05 — both required-still-passing per this iteration's own
  phase spec (`docs/phases/goal-ops-hardening-iter-5.md`, "Required-still-passing journeys: J-01, J-03,
  J-04, J-05") — were not replayed at all** in this artifact. Two of four required journeys have zero
  regression evidence this cycle.
- The dev handoff's Definition-of-Done self-check explicitly leaves J-01/J-03/J-04/J-05 confirmation as
  "not this step's job... QA's" and asserts "no regression is expected" because the diff avoids the
  *existing* protected call sites. The actual replay evidence contradicts that expectation for J-01 — this
  is precisely the gap this review exists to catch: a developer's textual claim of safety versus what
  replay evidence actually shows.
- `runs/goal-session-ops-hardening/state/journey-history.json` still shows J-01 as `"status": "passing"`
  with `"last_verified_iter": "goal-ops-hardening-iter-4"` — it has not yet been updated to reflect this
  iteration's failing replay, meaning the session's own tracked journey state is currently stale/wrong
  relative to the newest evidence.

### Other regression-risk surfaces checked, low/no risk

- `readiness.py`, `health-badge.tsx`, `scripts/start-backend.sh`'s enforced fields, `ensure_latest_snapshot`
  — confirmed untouched by this iteration's diff (matches the dev handoff's own claim and the plan's Out of
  Scope list). No risk to J-04's readiness-badge rendering path specifically.
- `/backtest` page's existing `BacktestSkeleton` loading idiom — unchanged, still present, now simply
  triggers for a much shorter window given the ~252x latency improvement. No regression.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Status |
|---|---|---|
| `ForwardAggregateCache` (new ingest-time cache) | `/backtest` page loads in <1s instead of ~35s (same numbers, byte-identical) | Fully exposed — documented in `user-visible-changes.md` |
| `_refresh_ingest_aggregates`'s new `forward_aggregates` warm step | `/data`'s "Refreshed: ..." line gains "forward aggregates" (3 render sites) | Fully exposed |
| Longer backfill/rebuild job duration (up to ~35-40s more) | Job card's "updated Ns ago" heartbeat keeps refreshing (per F1 reuse); job simply takes longer to reach "completed" | Documented in `user-visible-changes.md` as an explicit "What Old Behavior Changed" item — correctly disclosed, not hidden |
| 7 newly-measured pages' latency numbers | `reports/perf-budgets.md` only (explicitly an engineering artifact per spec, not a UI surface) | Correctly scoped as backend-only — spec itself classifies this as non-UI, so no gap |
| `/api/runs` N+1 pattern (measured, not fixed) | No UI change — audited and left as-is per spec's own "don't expand scope" instruction | Correctly scoped |

No unexposed backend capability found. This axis is clean — `implementation-summary.md` and
`user-visible-changes.md` agree closely, including on the "None — nothing new sitting unused" backend-only
claim.

---

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- **J-01 "Backfill honors the requested range and explains zero-work" (P1, required-still-passing) — FAILED
  its deterministic golden-script replay** this iteration (`reports/phase-goal-ops-hardening-iter-5-regression-replay-results.md`,
  step 06: expected text "2026-05-15" on `/scanner-runs` did not appear). This is the newest evidence in
  the iteration's pipeline (post-dates the review and QA reports) and is unresolved — no LLM fallback ran,
  no explanation was written anywhere, and `journey-history.json` has not been updated to reflect it.
  Correlated shared surface: `/scanner-runs`, `/api/runs`, the `ScannerRun` table — this iteration's own
  measurement harness ran four additional real backfill jobs against the same table this iteration also
  measured (TC-09). Action: investigate before this iteration is considered closed — confirm whether J-01's
  script needs updating for a now-much-deeper run history (test-side fix) or whether something in this
  iteration's repeated-backfill measurement methodology altered/paginated the run list in a way real users
  would also hit.
- **J-04 and J-05 (both required-still-passing) received zero regression-replay coverage** this cycle — only
  J-01 and J-03 appear in `regression-replay-results.md`. Given J-04/J-05 share the exact
  `_refresh_ingest_aggregates` function this iteration modified (see Regression Risk above), their absence
  from this cycle's replay evidence is a coverage gap, not a confirmed pass. Action: run the J-04/J-05
  golden scripts before treating this iteration as regression-clean.
- **Medium risk, mitigated:** `_refresh_ingest_aggregates` (shared by J-04/J-05) gained a new ~35-40s-per-ingest
  block. The developer correctly reused the F1 `prog.tick()` heartbeat pattern per horizon, which lowers
  the risk of J-04's heartbeat-freshness check regressing, but this is unverified by any replay evidence
  produced this cycle (see above).

### Visual Consistency
- No new pages or components were added, so there is nothing new to check against DESIGN SYSTEM tokens.
  The one changed page effect (`/backtest` populating almost instantly instead of after ~35s) reuses the
  pre-existing `BacktestSkeleton` loading idiom unchanged — consistent with prior phases' established
  pattern, per the plan's own explicit constraint ("extend the SAME idiom already on that exact page").
- Worth noting for context (not a new-page consistency issue, since this endpoint's code was untouched):
  QA's TC-02 finding that the Dashboard's `PhaseCrossViewCard` (`/api/indexes?full=true`) takes 1.68-2.19s
  under real browser conditions, over its 1.5s budget — on the home page, 0 clicks from anywhere. It does
  correctly show an honest `animate-pulse` skeleton (not a blank/frozen frame) while loading, so it
  satisfies the *substance* of what TC-14 asks for even while missing the *number* — this is QA's blocker
  to resolve, not a discoverability or regression defect in this review's scope, but it is the reason the
  iteration's home page currently has a visibly slower secondary panel than its committed budget states.

---

## Recommendation

1. **Do not treat this iteration as UX-clean until J-01's replay failure is explained or fixed.** At minimum,
   re-run the J-01 golden script (or its LLM fallback) against a stable, non-measurement-perturbed DB state
   and confirm whether "2026-05-15" is genuinely still reachable on `/scanner-runs`. If the run history has
   simply grown past what the script's fixed assertion anticipated, update the golden script rather than
   leaving a required-still-passing journey in an unconfirmed state.
2. **Run the J-04 and J-05 golden-script replays** — they were skipped entirely this cycle despite being
   required-still-passing, and they share the exact backend function this iteration modified.
3. Once J-01/J-04/J-05 are confirmed clean (or fixed), update `runs/goal-session-ops-hardening/state/journey-history.json`
   to reflect the actual outcome rather than leaving it stamped at iter-4.
4. No frontend action needed — discoverability and UI/backend parity are both clean this iteration.
