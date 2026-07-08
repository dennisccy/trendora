# Iteration 21 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The verification-only re-run succeeded exactly as specced: the canonical `browser-qa-agent` lane
ran **live** this time (it correctly overrode a stale dispatch SKIP flag by independently
re-verifying both services at HTTP 200), producing the non-empty, md5-distinct evidence dir that
iter-20 lacked, and **J-13 flips `partial → passing`** — every DoD-named J-13 case passed live with
DOM/computed-style precision, and CLOSURE-PASS cleared. Four of five required-still-passing replays
(J-01/J-03/J-05/J-10) came back live-clean, closing iter-20's replay gap. The two literal UT
failures (UT-16 P2, UT-21 P1) are independently verified **non-regressions on non-J-13 cases** — a
compliant coarser honest-degrade gate, and a mistargeted test reference to `/methodology` whose
Universe Selection section is correctly suppressed by a pre-existing anti-fabrication gate. Not
GOAL_ACHIEVED because J-02/J-06/J-07/J-08/J-09 remain goal.md-sanctioned `partial` and J-14/J-15/J-16
are `unknown`/unbuilt.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (live-replayed UT-17) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-17-sector-sort.png |
| J-02 | partial | partial (sanctioned; out of scope) | ledgers all-FAIL (git-unchanged) — no Proven badge to drill |
| J-03 | passing | passing (live-replayed UT-18) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-17-sector-sort.png (all "Not yet proven") |
| J-04 | passing | passing (byte-identity carry; untouched) | reports/qa/goal-mcp-loop-iter-19-evidence/UT-20-21-evidence-result.png |
| J-05 | passing | passing (live-replayed UT-19) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-19-evidence.png |
| J-06 | partial | partial (sanctioned; out of scope) | canonical ledger row 4 = FAIL (git-unchanged) |
| J-07 | partial | partial (sanctioned; out of scope) | canonical ledger row 5 = FAIL (git-unchanged) |
| J-08 | partial | partial (sanctioned; out of scope) | canonical ledger row 6 = FAIL (git-unchanged) |
| J-09 | partial | partial (sanctioned; out of scope) | canonical ledger row 7 = FAIL (git-unchanged) |
| J-10 | passing | passing (live-replayed UT-20) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-20-nvda-full-history.png |
| J-11 | passing | passing (byte-identity carry; ledgers all-FAIL confirmed) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-19-evidence.png |
| J-12 | passing | passing (substantive capability live-verified; UT-21 literal FAIL = mistargeted test, NOT a regression) | reports/qa/goal-mcp-loop-iter-21-evidence/UT-17-sector-sort.png (/stocks "541/541"); /data "541" per ui-test-results.md |
| **J-13** | **partial** | **passing (target — clean canonical live browser-qa)** | reports/qa/goal-mcp-loop-iter-21-evidence/UT-10-legend-two-groups.png |
| J-14 | unknown | unknown (unbuilt; out of scope) | n/a |
| J-15 | unknown | unknown (unbuilt; out of scope) | n/a |
| J-16 | unknown | unknown (unbuilt; out of scope) | n/a |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 No unbacked "proven"; unbacked ⇒ "not yet proven" | OK | Both ledgers all-FAIL (evaluator: canonical 7/0-PASS/7-FAIL, staging 7-FAIL, git-unchanged); UT-18 + UT-17 pixel show every score "Not yet proven". |
| #2 Decision-quality only; no return/price/buy-sell/orders | OK | Rendered `/data` header reads "Research-only · decision support · no orders" (UT-10 pixel); audit confirms no such language in legend/caption/tooltip copy. |
| #3 Displayed numbers correct (match engine) | OK | `test_compute_availability_byte_identical_after_fetch_scope_widening` PASS (102/102); /data 541 == /stocks 541/541. |
| #4 No overfit edges (survived referee) | OK | Zero PASS rows in either ledger; no `## Evidence Claim` submitted this iter. |
| #5 Determinism + no-lookahead preserved | OK | Zero engine/source diff vs HEAD (verification-only). |
| #6 No iteration ships evidence-claims without a referee PASS | OK | No Evidence Claim; gate passes automatically; ledgers untouched. |
| #7 No hard-coded credentials/keys/tokens | OK | scan-report.md = CLEAN on the full diff (only README prose + harness bookkeeping). |
| #8 Resilience to data-shape/scale; graceful degrade, never blank crash | OK | UT-16: backend-down shows an honest "Backend unavailable / … No figures … rather than fabricated values" card, sidebar/nav intact, no blank application-error, no fabricated data — satisfies anti-goal #8 (the literal FAIL is only against the test's per-card text; concurred by browser-qa, ux-regression, audit, closure). |

**Severity:** none. No violation, minor or critical.

## Next-Step Recommendation

**iter-22 (FULL).** J-13 is the last non-evidence journey to close; the extended goal is not yet met.
Remaining tractable scope, in recommended priority order:

1. **J-14 (deep index/macro context + per-series vendor labels)** — the most READY forward-feature:
   its step-1 data basis is already staged/committed (iter-17: `_SPX`/`_NDX`/`_DJI` deep, `_VIX` deep
   from Yahoo, `_TNX`/`_DXY`/`_VXN` FRED-macro proxies, vendors in `meta.json`). Steps 2–3 render the
   deep benchmark + macro overlays across the deep window with per-series vendor disclosure, registering
   the vendor-label Data Contract value. FULL (new user-facing surface + a new Data Contract value →
   needs coherence/audit/ux-regression/closure).
2. **J-15/J-16 (fast-platform perf budgets)** — commit the measurement harness (`scripts/measure-perf.sh`,
   item K) + budgets, land the mechanical backend pass (items B/C/D/G/H), re-measure ≥30% improvement,
   all byte-identical. FULL (data-path change, byte-identity-gated).
3. **Re-certify J-02/J-06/J-07/J-08/J-09 on the 30-year basis** — the riskiest: re-run the pre-registered
   staging exploration on the new data and promote ONLY a winner whose recorded block-bootstrap `p`
   clears the canonical Bonferroni bar (now divisor 8) with margin, via an explicit `"ledger":"canonical"`
   `## Evidence Claim`; honor the honest-stop guard. Do NOT casually append a canonical claim.

**Non-blocking follow-ups to file (do NOT reopen J-13):**
- Retarget UT-21's universe-count-consistency check at `/data` ("Universe (as of date)") vs `/stocks`
  ("{visible}/{total}"), OR gate the `/methodology` check on `apps/backend/data/seed/universe.json`
  existing, so "section correctly absent" scores PASS rather than failing every future J-12 replay.
- Loosen UT-16's expected text to the actual compliant page-level "Backend unavailable" gate, or add a
  request-interception-capable QA tool for the narrower single-endpoint-failure branch.
- Carry the `start-frontend.sh` freshness-stamp gap (iter-20 audit O1); the `rm -rf apps/frontend/.next`
  workaround remains the operational mitigation.

## Halt Justification (if halting)

N/A — CONTINUE. Not GOAL_ACHIEVED: J-02/J-06/J-07/J-08/J-09 are `partial` and J-14/J-15/J-16 are
`unknown`, so not every Must-have journey is `passing`. Not REGRESSION: no journey moved
`passing`→`failing` (J-12's substantive capability is intact — the UT-21 literal FAIL targets a page
J-12's canonical golden script never used, and the `/methodology` suppression is a pre-existing
anti-fabrication gate untouched by iter-20/21), and no critical anti-goal was violated. Not STALLED:
the blocker was operationally fixable (services down + stale bundle) and was fixed, with clear tractable
next work. Not ESCALATE: already full; review PASSED (not fail-open); no journey failed two consecutive
iterations. Coherence is COHERENCE-PASS (no structural veto, no consolidation owed).
