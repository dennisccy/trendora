# Iteration 5 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-5 delivered the **immutable scanner-run persistence spine** — the product's evidence-tracking
foundation — and lit up **J-07** (Risk-Off run shows zero Actionable) and **J-08** (immutable as-of
run history; older differs from latest). Both target journeys verified directly from on-disk evidence
(I viewed the scanner-runs list + the older/latest detail captures) plus unit/API proofs and a clean
source read; J-01–J-06 re-shot and hold green; coherence is **PASS** and no anti-goal — including all
four criticals exercised this iteration (immutable / no-lookahead / single-source / risk-off-gates-
actionable) — was violated. Not GOAL_ACHIEVED: J-09/J-10/J-11 remain unbuilt by design → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Dashboard | passing | **passing** (re-shot) | TC-15-j01-dashboard.png — regime 74.32 Risk-on + 5 components, breadth 65.57%/59.02% (universe-relative), counts 0/8/1, 5 sectors, 5 themes, as-of 2026-05-28 |
| J-02 Stock Leaderboard | passing | **passing** (re-shot) | TC-15-j02-stocks.png — 122 ranked rows; QA filters PASS (MU A/94.50) |
| J-03 Theme Leaderboard | passing | **passing** (re-shot) | TC-15-j03-themes.png — 11 ranked themes; dashboard Top Themes corroborates |
| J-04 Sector Leaderboard | passing | **passing** (re-shot) | TC-15-j04-sectors.png — 31 ranked ETFs; dashboard Top Sectors corroborates |
| J-05 Stock Detail | passing | **passing** (re-shot) | TC-15-j05-stock-detail.png — MU chart + 3 score cards + invalidation |
| J-06 Score consistency | passing | **passing** (strengthened) | QA deep-compare MU 94.5 across leaderboard / /api/stocks/MU / **stored snapshot run-3**; `test_latest_run_faithful_to_live_computation`; coherence.md Part A PASS |
| **J-07 Risk-Off → 0 Actionable** | failing | **passing (NEW)** | TC-11-scanner-runs-list.png (both Risk-off runs Actionable=0) + TC-12-risk-off-detail.png; `test_risk_off_run_has_zero_actionable` + API J-07 test |
| **J-08 Immutable run history** | failing | **passing (NEW)** | TC-11 (3 dated runs DESC) + TC-13-older.png (regime 8.34) vs TC-13-latest.png (regime 74.32); `test_runs_are_distinct_as_of_snapshots` + API J-08 test |
| J-09 System Health | failing | failing (not targeted — iter-6) | — |
| J-10 Control-group honesty | failing | failing (not targeted — iter-6) | — |
| J-11 Watchlist | failing | failing (not targeted — iter-7) | — |

**Deltas:** Newly passing **J-07, J-08**. Newly failing: none. Regressed: none. J-01–J-06 held green
(and J-01–J-05 freshly re-verified rather than carried).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Snapshots immutable *(critical — first real test)* | OK | `scanner.py` uses only `session.add()` INSERTs + commit — no UPDATE/merge/delete/setattr on any fetched run (grep-confirmed); `run_scan` returns the existing run unchanged for a known date. `test_run_scan_idempotent_and_immutable` + `test_bootstrap_runs_idempotent_persists_all_dates` PASS |
| No lookahead *(critical)* | OK | Engines read via `bars_asof` (date ≤ asof); `test_run_scan_no_lookahead` proves a run dated D == the run against a DB truncated to ≤ D |
| Single source of truth *(critical — headline risk)* | OK | `scanner.py:64-84` calls each engine once, reads breadth/counts from `score_regime`/`summarize_candidates` (no 2nd formula); `record_json` faithful copy; `runs.py:64` serves stored rows only. `test_latest_run_faithful_to_live_computation` field-by-field PASS; coherence Part A PASS |
| Risk-Off gates Actionable *(critical)* | OK | Both Risk-off runs show 0 Actionable (TC-11 + unit `{Risk-off-watchlist: 122}`) |
| No magic numbers | OK | `test_scanner_has_no_scoring_or_date_literals` PASS; bootstrap dates from `config.scanner.bootstrap_dates` |
| No fabricated data | OK | Unknown run → 404, no price data → 503 (both tested); breadth labelled `universe-relative` |
| No order/execution path *(critical)* | OK | grep for broker/order/execute/capital-deploy in `app/` + `main.py` → empty |
| No secrets in source | OK | grep for hardcoded key/secret/token → empty |
| Honest limitations surfaced | OK | breadth + new-high/low tagged `universe-relative` on dashboard and run detail |

**Coherence audit:** `iter-5/coherence.md` = **COHERENCE-PASS** (Part A data-contract PASS, Part B IA
PASS). No structural veto.

## Next-Step Recommendation

**iter-6 at `full` depth — J-09 + J-10 (the walk-forward forward-testing engine + System Health).**
This is the keystone "prove its own usefulness" capability and the hardest no-lookahead test yet:

- A **separate append-only `forward_returns` table keyed to `(run_id, ticker, horizon)`** — designed-
  but-not-created this iter; it MUST NOT mutate the snapshot (the immutability guarantee built here).
- Walk-forward replay that scores as-of past dates with strict no-lookahead (date ≤ D for scoring) and
  measures realized 1/5/10/20/60-day forward returns using **only** bars with date > D — unit-prove the
  boundary, exactly as `bars_asof` already enforces for scoring.
- Aggregations computed **once** by the forward-testing engine: forward return by bucket (A–E), by
  setup, by regime; excess vs SPY/QQQ/sector ETF; and the **random-same-sector control group** so
  selection is visibly separated from sector beta. Surface `n` (sample size) and the survivorship-bias
  label (Honest-limitations anti-goal).
- New **`/system-health`** page (currently an EmptyState stub) + canonical `/api/forward-returns`-style
  endpoints. The snapshot store will need ≥1 mid-history Risk-on run too, so there are enough as-of
  dates for a meaningful forward-return sample.

**Recurring process fixes the orchestrator/harness still owes (NOT product code) — now chronic:**
1. **Emit the audit handoff.** `reports/audits/` does not even exist — the audit handoff has been
   missing **5 consecutive full-depth iterations**, and iter-5 put it in the spec's Definition of Done,
   yet it still did not run. A spec/DoD-level ask has now demonstrably failed to fix it; the fix must be
   in the runner script, not the spec text.
2. **Make the dedicated browser-qa own/self-heal its frontend.** The SKIP-on-HTTP-000 flap recurred a
   **5th** time (dedicated report 0/19 SKIPPED; QA mode-2 self-healed and persisted all 10 evidence
   PNGs). Reconciled from on-disk evidence + unit proofs per the standing lesson — but the structural
   harness fix is still owed.

Neither gap affected this verdict: journeys were verified from persisted evidence + unit/API tests +
direct source reads, and anti-goals from `git diff`/greps.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: two journeys newly passing (J-07, J-08), no regression, no anti-goal
violation, coherence PASS, and a clear, tractable next target (J-09/J-10). GOAL_ACHIEVED is withheld
because J-09, J-10, and J-11 are not yet built (by design).
