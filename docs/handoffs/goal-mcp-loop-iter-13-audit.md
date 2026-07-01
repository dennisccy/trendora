# goal-mcp-loop-iter-13 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08's core capability is achieved and browser-verified: the composite-cohort "Proven" badge flips correctly
for the certified `rs_spy_3m × high_proximity` @ h20 selection, honestly reads "Not yet proven" for every
other combination/horizon, the `/evidence` combination row renders with verbatim ledger fields, and the
signal-less claim lights no `/stocks` badge. The one browser-qa FAIL (deep-link anchor does not scroll its
row into view) is a **pre-existing, product-wide** platform gap shared by every evidence deep-link — NOT
introduced by iter-13 — which I fixed surgically during this audit. The remaining gap is that my scroll fix
awaits a browser-qa re-run to confirm UT-05/UT-14 flip to PASS.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): zero app-code change; the 6th canonical PASS is gate-written and honest.**
`git diff HEAD -- apps/backend/app/` is empty — the referee, `verify_edge`, `online_fdr`, `evidence.py`, and
`api/evidence.py` are byte-unmodified. The ledger diff (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`)
is exactly **one appended line** (row 6, the combination PASS); the prior 5 rows are byte-identical (git
reports `1 insertion(+)`). Row 6 (`certified-claims.jsonl:6`) is a genuine PASS: Bonferroni `deflation_divisor=6`,
`required_p=0.008333`, `p_value=0.0009995 < required_p` (~8× margin), `holdout_edge=+0.046932`,
`control_excess=+0.046932`, `status=PASS` — the honest-stop guard is satisfied (a real PASS, not a forced
promotion). Backend suite `test_evidence.py`+`test_api_evidence.py`+`test_staging_ledger_routing.py` = **36
passed**.

**B2 — OBSERVATION (verified): the online-FDR golden change is honest bookkeeping, not a masked behavior change.**
`apps/backend/tests/test_staging_ledger_routing.py` updates the live-canonical goldens `rejection_offsets`
`[1,2,4,5] → [1,2,4,5,6]` and `count_trials 5 → 6`. This adds ordinal 6 only; `ma_stack` (line 3) stays FAIL
and no prior ordinal is rewritten — exactly consistent with a single new PASS appended. Test-only; no `app/**`
logic touched.

### Frontend Findings

**F1 — IMPORTANT (fixed): deep-link anchor does not scroll its `/evidence` row into view.**
Browser-qa `UT-05` + `UT-14` failed: clicking the "Proven" badge (and direct navigation to
`/evidence#combination-high_proximity-rs_spy_3m-h20`) set the correct URL hash and the row was present at
`top=1585px`, but `window.scrollY` stayed `0`. Root cause verified in `apps/frontend/app/evidence/page.tsx`:
the page fetches claims async (`useEffect`, lines 39-48) and renders `ClaimRow`s only after the fetch resolves
(lines 76-82). The browser's native one-shot hash-scroll fires before those rows exist in the DOM, so it never
lands. There was **no** JS hash-scroll effect — only the `id={anchorId}` + `scroll-mt-20` on each `ClaimRow`
(line 143), which shows anchor-scroll was *intended* but left incomplete. This gap is **pre-existing and
product-wide**: every evidence deep-link uses the same `ClaimRow` (signal J-02/J-05 `signal-…`, factor
J-06/J-07 `factor-…`, combination J-08 `combination-…`), so all suffer it equally. `app/evidence/page.tsx` is
NOT in `changed_files` — iter-13 neither caused nor worsened it.
**Fix applied:** added an additive hash-scroll `useEffect` (keyed on the load→ok transition) that reads the
URL hash and `scrollIntoView`s the matching row once it mounts. It is a no-op when there is no hash or no
matching row (never fabricates scroll), respects each row's `scroll-mt-20` offset, and fixes the deep-link
landing for **all** evidence anchors, not just the combination row. Verified: `tsc --noEmit` clean;
`lib/evidence.test.ts` still 37/37.

**F2 — OBSERVATION (verified): the combination matcher + badge wiring is correct end-to-end.**
`lib/evidence.ts` `resolveCombinationEvidence` (lines 579-605) matches on `kind`+`cohort`+**order-independent
full-leg set** (`combinationLegKey`, sorted full `factor:side:quantile` strings — line 538) + `horizon` +
`direction`, re-displays `entry.proven` verbatim, and is fail-safe (matched-but-non-PASS / empty / null →
"Not yet proven"). `combinationClaimId` (line 548) yields a deterministic, `combination-`-prefixed anchor
distinct from any `factor-…`. `_labs.tsx` `CombinationTable` (lines 1439-1455) builds the cohort from the
backend-resolved `data.conditions` in the exact `${factor.key}:${side}:${quantile.key}` byte-format, hardcodes
`direction:"positive"` (correct — the composite is the top-quantile blend, positive by construction), and
renders the badge only on the composite row. Browser-qa `UT-03/08/09` confirm the flip works against the real
backend — which also **empirically proves the leg byte-format matches the ledger** (`quantile.key` = "quintile"/"tertile").

### Test Findings

**T1 — IMPORTANT (observation, no code fix needed): the QA report's central browser claim is FALSE.**
`reports/qa/goal-mcp-loop-iter-13-qa.md` (verdict PASS_WITH_NOTES) claims the badge "currently reads 'Not yet
proven' even when composed with the certified selection" and hand-waves it as a "runtime timing / state race
condition." This is **wrong**. The canonical `browser-qa-agent` lane
(`reports/phase-goal-mcp-loop-iter-13-ui-test-results.md`) tested the certified selection against the real
backend and recorded `UT-03` **PASS** (`<a data-proven="true" href="/evidence#combination-high_proximity-rs_spy_3m-h20">Proven</a>`),
plus `UT-08` (reactive flip) and `UT-09` (horizon-sensitivity) PASS. The qa.md agent evidently failed to
compose the certified pair (it must swap leg 2 to `high_proximity:top:tertile` — the default `rs_spy_3m ×
atr_pct` is a FAILED pair). There is no timing race in the code. Future readers should trust the browser-qa
results file over qa.md on this point.

**T2 — OBSERVATION (verified): unit + backend assertions are tight.**
`lib/evidence.test.ts` (+10 combination checks) pins the exact anchor, exact order-independent leg-set,
matched-but-non-PASS, and empty/null paths; the backend test asserts the served row byte-matches the ledger
(`signal:null`, `proven:true`) and stays absent from `proven_signals`. No loose "accepts either outcome"
assertions found.

---

## 3. Domain Assessment

The evidence layer correctly extends from single-factor/single-horizon proofs to a **composite (multi-factor)**
proof without ever recomputing proven-ness: the referee's verdict is re-displayed verbatim on both surfaces,
and the UI's `resolveCombinationEvidence` only *reads* `entry.proven`. The promotion is statistically honest —
the Bonferroni divisor-6 bar (`required_p=0.008333`) is cleared with an ~8× margin and the `+4.69%` holdout
edge is modest and credible (not a p-floor-saturated outsized-edge flag). The claim is correctly **signal-less**
(`_resolve_signal → None`), so it backs the combination lab + `/evidence` only and lights no per-stock badge
(`proven_signals` stays `{leadership_score}`, confirmed by `UT-12` and backend TC-02). Determinism / no-lookahead
are preserved (no engine change). All seven anti-goals hold; no return/price/buy-sell language (title
`rs_spy_3m × high_proximity — composite`, subtitle `Out-of-sample edge — multi-factor composite`).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/evidence/page.tsx` | Added an additive hash-scroll `useEffect` (gated on the load→ok transition) so a "Proven" deep-link scrolls its backing `ClaimRow` into view after the async claims mount. Completes the intended-but-incomplete `scroll-mt-20` anchor feature; lands the deep-link for **all** evidence anchors (signal / factor / combination). No structural change to row rendering. Verified: `tsc --noEmit` clean; `lib/evidence.test.ts` 37/37. |

---

## 5. Recommended Next Step

Re-run the `browser-qa-agent` lane to confirm the scroll fix flips `UT-05`/`UT-14` from FAIL to PASS (I
verified the fix via typecheck + unit tests + root-cause soundness, but not a live browser scroll — the
services were down at audit time and the pipeline re-runs this lane). With that confirmation, J-08 lands fully
browser-verified (Proven badge + honest not-yet-proven + verbatim `/evidence` row + landing deep-link) with
J-01..J-07 non-regressed and no anti-goal violation — the goal-evaluator can then assess GOAL_ACHIEVED, as
J-08 is the sole remaining Must-have journey. No blocking backend or correctness work remains.
