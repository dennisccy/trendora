# goal-ops-hardening-iter-5 Audit Report

**Date:** 2026-07-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

This iteration's substantive deliverable — the J-06 measurement pass plus the ONE contingent
backend fix it authorized — is correct and materially strengthens the product: the spec's own
highest-risk candidate, `GET /api/backtest`, was a genuine measured violation (34.766s, 5×
full-partition scans of `forward_returns`) and is now served from an ingest-warmed
`ForwardAggregateCache` at 0.138s (~252×), byte-identical to the live compute, with tight tests I
independently confirmed are not passing by accident. Two gaps remain and both are documented, not
hidden: (a) `/api/indexes?full=true` on the Dashboard measures 1.68–2.19s in a real browser (over its
1.5s budget) due to browser connection-queuing — a pre-existing, untouched-by-this-iteration endpoint
whose fix is explicitly out of this iteration's authorized scope; and (b) the J-01 deterministic
replay missed, which I traced to a stale test-harness proxy assertion, **not** a real regression (I
verified the run data is intact and the runs-display code path was never touched). Because the work
that was built is correct and no critical/data/security defect exists, this is PASS_WITH_GAPS — but
note clearly for the downstream evaluator: **J-06 cannot be declared "passing" until the two gaps in
§2 are resolved by a fresh iteration** (they are not fixable within this iteration's spec scope).

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, out-of-scope): `/api/indexes?full=true` exceeds its 1.5s committed budget under real-browser load.**
`reports/phase-goal-ops-hardening-iter-5-ui-test-results.md` (TC-02) records 1678/2185/2054ms across
3 real-browser reloads vs. an ≤1.5s committed budget, reproducible 3/3. Root-caused (measured, not
speculative): curl-isolated and a 10-request concurrent curl burst both stay in budget (0.79–0.95s);
the extra ~0.8–1.2s is browser-side connection-queue wait (Chrome's 6-conns-per-origin cap against
HTTP/1.1 uvicorn while the Dashboard fires 10–13 same-origin requests in one ~10ms window). Verified
against source: this endpoint is served by `compute_index_series` over a small CONFIG-FIXED set of
index ETFs (`apps/backend/app/api/backtest.py`-adjacent handler; audited in the dev handoff's TC-13
table) — it is **not** an unbounded `daily_prices`/`forward_returns` scan, and it was **not** touched
by this iteration's diff (`git diff HEAD` shows no change to the indexes path). The page degrades
honestly: `apps/frontend/components/phase-cross-view-card.tsx` renders its own `animate-pulse`
skeleton while this secondary panel loads, so the substance of TC-14 (never blank/frozen) is met even
while the *number* is missed. **Not fixed, deliberately:** the only real fixes (HTTP/2 on uvicorn,
request batching/coalescing, or a browser-realistic budget re-commit) are architectural changes the
spec expressly forbids this iteration from making ("If a measured violation's fix does not fit the
mechanical ingest-time-cache pattern … STOP … hand back to a fresh decomposer iteration"). Attempting
it here would be the scope creep the spec prohibits. Hand to a fresh iteration.

**B2 — GAP (observation): `/scanner-runs` renders all 750 runs unpaginated with an N+1 count query per run.**
`apps/backend/app/api/runs.py:31-46` issues `select(ScannerRun)` (no LIMIT) plus one
`select(func.count()).where(run_id==...)` per run, and `apps/frontend/app/scanner-runs/page.tsx:85`
maps every returned run into the DOM with no pagination. I confirmed the DB now holds **750**
scanner_runs (asof range 2005-02-25 … 2026-07-17), up from the ~180 the spec assumed. This is
pre-existing (both files unchanged this iteration), was correctly measured and consciously left
un-fixed in the dev handoff's TC-13 audit (not the mechanical pattern; not on the deep
`daily_prices` basis, so not an AG-8 violation), and browser-QA TC-09 still passed it in budget
(142+148ms). Recorded as a latent scalability concern — it is also the mechanism behind the T1
replay brittleness below. A secondary instance of B1's browser-queuing pattern was also flagged
honestly by QA: `/api/data/availability` reads ~2.9–3.0s in-browser vs ~0.95s curl, on its own
independent spinner — same class, same graceful-degradation, same out-of-scope disposition.

*(No credential/network findings: the change is a pure DB-read cache — AG-7/AG-9 clean; the existing
`test_finalize_hook_makes_no_network_call` passed with the new code, per the finalize-hook cluster
re-run.)*

### Frontend Findings

**F1 — (no finding): zero frontend diff, correctly.** `git diff HEAD -- apps/frontend/` is empty.
The contingent loading-state work (TC-14) was never triggered because `/backtest`'s page already
carries `{kind:"loading"}` + `<BacktestSkeleton/>`, and the two over-budget panels (B1, B2) already
render their own honest skeletons/spinners. This matches the plan's "if no page exceeds budget, no
frontend code changes" branch. Correct.

### Test Findings

**T1 — GAP (test-harness brittleness, NOT a product regression): J-01 deterministic replay failed at step 06.**
`reports/phase-goal-ops-hardening-iter-5-regression-replay-results.md` records J-01 FAIL — step 06
(`goto /scanner-runs`, expect text `"2026-05-15"`) did not find the text; `journey-scripts/J-01.json`
confirms that literal, unrelated-to-the-submitted-backfill assertion (a "run history intact" proxy).
I investigated rather than accept either the "regression" or "flake" label:
- **The run data is intact.** Direct DB query: exactly **1** scanner_run at `2026-05-15` exists (plus
  the full May-2026 series). No data was lost.
- **The runs-display code path was never touched.** `runs.py`, `scanner-runs/page.tsx`, `/api/runs`,
  and the `ScannerRun` schema are all outside this iteration's `changed_files`. The page renders every
  run (`formatIsoDate` emits `yyyy-MM-dd`, so `"2026-05-15"` *is* in the DOM when the fetch resolves).
- **Same page passed elsewhere this cycle:** browser-QA TC-09 loaded `/scanner-runs` and passed.

Conclusion: whatever caused the miss (most plausibly a render/latency-timing artifact of the now-750-row
unpaginated table under the deterministic runner's step timeout — see B2), **it is not attributable to
this iteration's changes and is not a real regression.** It is nonetheless an unmet DoD-evidence item:
the deterministic replay missed and no LLM-fallback adjudication ran. **Not fixed by me, deliberately:**
editing the session-level golden script to make the gate go green is a gate-weakening action I could
not re-verify without standing up the full prod stack (backend is down; the DB has since drifted to 750
runs), and re-running browser replays is QA's lane, not the auditor's. Requires: update J-01's proxy
assertion to be robust to a growing run history (or assert on data the submitted backfill actually
produces), then re-run — or run the LLM fallback the plan promised.

**T2 — GAP (coverage): J-04 and J-05 received zero regression-replay this cycle.**
`regression-replay-results.md` contains only J-01 and J-03; the spec's required-still-passing set is
J-01/J-03/J-04/J-05. J-04/J-05 both depend on `_refresh_ingest_aggregates`, which this iteration
modified — so their absence is a genuine coverage gap, not a confirmed pass. Mitigating code evidence
(which lowers, not eliminates, the risk): I read the diff directly — the new warm block reuses iter-4's
F1 `prog.tick()` heartbeat idiom once per horizon (protects J-04's heartbeat-freshness assertion), and
the change *precomputes forward aggregates at ingest* — which is exactly what J-05 ("aggregates
precomputed at ingest, never on the fly") asserts, so J-05 is reinforced, not threatened. Still: run
the J-04/J-05 golden scripts before asserting "regression-clean."

**T3 — OBSERVATION: `test_api_backtest.py`'s `loaded_engine` suite (incl. the 3 evidence-by-horizon tests) was not run to completion.**
Both dev and reviewer flagged the >10min session-fixture build. Compensating evidence is strong and I
credit it: 20 new/updated fast unit tests pass, plus a live byte-identity spot-check against the real
176,447-observation DB. The three directly-relevant tests exercise the *unchanged* producer
(`compute_forward_aggregates`), which the cache wraps without altering. Low risk, but the reviewer's
"run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` before merge" recommendation
stands.

**T4 — (positive, no defect): the new cache tests are tight.** I read them to confirm they don't pass
by accident: `test_forward_aggregates_cached_byte_identical_and_single_row` asserts
`json.dumps(sort_keys=True)` equality of fresh==miss==hit AND exactly one row;
`..._avoids_recompute_on_hit` uses a monkeypatch call-count proof (`==1`) that would catch a silent
recompute a byte-match would miss; `..._refreshes_on_dataset_version_change` mutates the dataset,
asserts the version bumps, asserts the recompute grows the cohort `n=6 → n=7`, and asserts the stale
row is pruned — a genuine invalidation test that directly discharges the iter-2 B1 lesson. The
finalize-hook zero-recompute invariant (`call_count == 0` after warm) mirrors the spec's requested
`..._zero_prefill_calls` pattern. This is the quality floor the spec's TC-17/TC-18 asked for.

---

## 3. Domain Assessment

The core domain logic — the `ForwardAggregateCache` fix — is correct and faithful to the codebase's
established conventions. Read directly (`models.py`, `forward_testing.py`):

- **Sole-producer preserved.** `forward_aggregates_cached` is a pure serving/persistence wrapper;
  `compute_forward_aggregates` is unchanged and remains the only derivation path. `/api/backtest` and
  the MCP `query_backtest` sibling both now call the wrapper (the latter is the disclosed, reviewer-
  accepted one-file scope extension — byte-identical call shape, low risk).
- **Correct invalidation (the highest-stakes property).** The key is
  `(horizon, asof_key, dataset_version)`, where `dataset_version` is the same global stamp
  `research._dataset_version` produces. Any dataset change (a backfill anywhere, including an earlier
  date entering a later as-of's expanding window) bumps the stamp, so a stale row is never *hit*, and
  is pruned on the next write for that key. This is the right answer to the iter-2 B1 failure mode
  (a fingerprint-only invalidation serving a false sentinel on a populated DB) and is proven by T4's
  invalidation test — not merely asserted.
- **Honest cold-miss contract.** A historical as-of not pre-warmed computes-once-then-caches, matching
  `EventStudyCache`/`MarketPhaseCache`. No fabricated value, no 500.
- **Live-verified.** I confirmed the DB holds exactly 5 `forward_aggregate_cache` rows keyed at the
  true latest run date (2026-07-17), one per configured horizon — the ingest warm fired correctly
  against real data, matching the dev handoff's claim.

The one honest trade-off (correctly disclosed by dev/reviewer/ux-regression, not minimized): the
unconditional per-ingest warm adds ~35–40s to every data-changing backfill. It is wrapped non-fatal
and heartbeat-ticked per horizon, so it cannot flip an ingest to failed and keeps J-04's heartbeat
fresh; on a no-data-change ingest it is a cheap cache hit. Acceptable for a 252× read-path win on the
capstone endpoint.

---

## 4. Fixes Applied During This Audit

None.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No code fixes applied — see rationale below. |

Rationale (disciplined non-action, per the auditor contract): the two blocking gaps are **not
surgically fixable within this iteration's authorized scope**. B1 (`/api/indexes` browser budget)
requires an architectural change (HTTP/2 / request batching / budget re-commit) that the spec
explicitly routes to a fresh decomposer iteration — fixing it here is prohibited scope creep. T1
(J-01 replay) is a proven false-negative whose only "fix" is editing a session-level golden script,
which (a) would be gate-weakening and (b) is unverifiable without standing up the full prod stack and
re-running the replay — and "a fix without re-run evidence is not a fix." The correct action for both
is documentation + hand-off, which this report provides.

---

## 5. Recommended Next Step

The backend fix is correct, well-tested, and shippable on its own merits. **Do not close J-06 as
"passing" on this iteration**, and do not expand this iteration to chase the residuals. Instead, open a
fresh decomposer iteration scoped to exactly two items:

1. **Resolve the Dashboard `/api/indexes?full=true` browser-concurrency budget (B1).** Decide between a
   real latency fix (HTTP/2 on the uvicorn launcher, or coalescing the Dashboard's 10–13 on-load calls)
   and a documented browser-realistic budget re-commit in `reports/perf-budgets.md`. Include
   `/api/data/availability` (same class) in the same decision.
2. **Restore clean regression evidence (T1/T2).** Make J-01's `/scanner-runs` proxy assertion robust to
   a growing (now 750-row) run history — or re-point it at data the submitted backfill actually
   produces — then re-run J-01, and run the skipped J-04/J-05 golden scripts. Once J-01/J-04/J-05 are
   confirmed, update `runs/goal-session-ops-hardening/state/journey-history.json` (still stamped at
   iter-4). Optionally revisit `/scanner-runs`' unpaginated 750-row render (B2) if that iteration
   touches the runs surface.

Before merge of *this* iteration's code, run the reviewer's flagged
`pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` to completion (T3).
