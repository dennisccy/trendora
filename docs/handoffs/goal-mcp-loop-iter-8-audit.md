# goal-mcp-loop-iter-8 Audit Report

**Date:** 2026-06-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The vcp_contraction top-decile (D10 @ h20) certified out-of-sample edge is genuinely surfaced as a "Proven"
badge on the Research factor lab and as a new claim row on `/evidence`, both reading the canonical
`GET /api/evidence` payload verbatim with zero recomputation and zero engine diff. I verified the certified
ledger entry, the pure read-side matcher, the shared anchor contract, the backend confirming test, and the
canonical browser-QA lane (17/18 PASS; the one P2 fail is a benign click-bubble nuance) — all six Must-have
journeys (J-01…J-06) are green and the displayed numbers byte-match the engine. No anti-goal violation
remains; the only open items are OBSERVATION-level and one non-gating demo-render gap.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): zero `app/**` diff; the certified entry is served by the existing pipeline.**
`runs/.../status.json` `changed_files` lists only `apps/backend/tests/test_evidence.py` under the backend
(no `apps/backend/app/**`). `apps/backend/app/engine/evidence.py` (`_resolve_signal` L69-85, `build_evidence_payload`
L110-130) is unchanged: a signal-less plain-factor cohort (`kind=factor`, `factor` ∉ `_SCORE_COLUMN_FACTORS`
L66) resolves to `None`, so vcp_contraction never enters `proven_signals`. This is the correct, spec-mandated
"no new computation, no new endpoint, Data Contract row 1 canonical" outcome — confirmed in code, not just
the handoff.

**B2 — verified: the certified ledger line is real and correct.**
`runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 4 = `factor:vcp_contraction`,
`slice_kind:decile`, `decile:10`, `horizon:20`, `direction:positive`, `status:PASS`,
`holdout_edge/control_excess = 0.03330492745744988` (+3.33%), `p_value = 0.011494252873563218`,
`deflation_divisor 4`, `required_p 0.0125`, `register_date 2026-06-30`, and crucially **no `signal` key**.
Line 3 is the `ma_stack` D10 FAIL (p 0.01949 ≥ 0.01667). The gate authority condition is satisfied.

**B3 — verified: the backend test is tight and byte-matches the ledger.**
`test_build_payload_vcp_contraction_factor_cohort_post_certification` (test_evidence.py L235-287) builds the
4-entry ledger and asserts `proven_signals.keys() == ["leadership_score"]`, `vcp.proven is True`,
`vcp.signal is None`, selectors verbatim, `vcp.verdict.holdout_edge == 0.03330492745744988`,
`p_value == 0.011494252873563218`, `ma.proven is False`, and `_resolve_signal(vcp) is None` /
`_resolve_signal(ma) is None`. The builder values byte-match the real ledger lines 3–4. Exact-value
assertions, not loose. 11/11 pass (QA Step 2).

### Frontend Findings

**F1 — OBSERVATION (honest, not a defect): `leadership_score` also reads "Proven" on the factor lab.**
`apps/backend/app/config.py` L198-200 puts both `leadership_score` and `vcp_contraction` in
`FACTOR_TYPED_COLUMNS`, so the factor lab lists `leadership_score` as a row. The general matcher
`resolveCohortEvidence` (`lib/evidence.ts` L406-435) therefore resolves its D10@h20 cohort to "Proven"
because the 1st ledger entry is a genuine PASS over exactly that cohort. The spec's parenthetical expectation
read "(vcp_contraction 'Proven', others 'Not yet proven')", but lighting `leadership_score` is **honest and
correct** — anti-goal #1 only forbids *unbacked* cohorts reading "Proven", and this one is certified. The
badge correctly deep-links to `/evidence#signal-leadership_score` (the row's real id), not a cohort anchor it
never carries — this is what `claimAnchorId` (L379-385) guarantees and what test case `q2` (test L457-468) +
canonical UT-08/UT-10 explicitly verify. The dev documented the decision; suppressing a true status would
have been the dishonest choice. No fix.

**F2 — OBSERVATION (P2 UX, non-blocking): clicking a passive "Not yet proven" chip expands the row.**
`FactorEvidenceBadge` (`_labs.tsx` L740-797) guards only the "Proven" `<Link>` with
`stopPropagation()` (L769-770); the "Not yet proven" path renders a bare `<Badge>` DIV (L784-795) with no
guard, so a click bubbles to the summary row's `onClick` toggle (L834). Canonical UT-09 caught this (P2,
"does not affect verdict"). It is benign: the chip is non-interactive (no link, no navigation), nothing
uncertified ever reads "Proven", no journey is affected, and the bubbled expand is the row's own existing
behavior. The "Proven" link is correctly isolated (UT-17 PASS). Not fixed — OBSERVATION-level UX polish, and
the behavior is arguably acceptable for a passive chip inside a click-to-expand row.

**F3 — OBSERVATION (code-quality): dead import `cohortEvidenceAnchor` in `_labs.tsx`.**
`_labs.tsx` L35 imports `cohortEvidenceAnchor` but never calls it (grep confirms only the import line matches;
the href is produced inside `resolveCohortEvidence` via `claimAnchorId`). `FactorCohort` (L38) and
`resolveCohortEvidence` (L39) ARE used. The reviewer flagged this as a NOTE; `tsc --noEmit` and `next build`
are clean, so it breaks nothing. Per auditor scope this is OBSERVATION-level — documented, not fixed.

**F4 — verified: the shared anchor contract makes every deep-link land, no collisions.**
`claimAnchorId` (`lib/evidence.ts` L379-385) is the single id both the `/evidence` `ClaimRow` (`evidence/page.tsx`
L140) and every badge agree on: score rows → `signal-${signal}`, signal-less factor cohorts → `factor-<f>-d<d>-h<h>`,
event-study → `null`. Resulting ids: vcp `factor-vcp_contraction-d10-h20`, leadership `signal-leadership_score`,
ma_stack `factor-ma_stack-d10-h20`, Breakout-watch none — all distinct. Canonical UT-04/UT-06/UT-08/UT-13
confirm the live anchors scroll into view.

**F5 — verified: claimSurface factor branch is honest; score + event-study branches byte-identical.**
`claimSurface` (`lib/evidence.ts` L257-304) routes a signal-less `kind:factor` cohort to title
`"<factor> — top decile (D<d>)"`, subtitle `"Out-of-sample edge — factor top decile"` (no buy/sell/return
language — anti-goal #2), and the `/research/factor-lab` linkback. The score branch (L258-266) and event-study
branch (L272-281) are untouched. Test cases `s`/`t` (L481-509) assert byte-identity for J-04/J-05; canonical
UT-12 (ma_stack framing), UT-13 (leadership "Stocks leaderboard"), UT-14 (Breakout-watch event-study linkback)
confirm live.

### Test Findings

**T1 — verified: frontend unit coverage is tight and edge-complete.**
`lib/evidence.test.ts` (25 cases) asserts exact hrefs (`/evidence#factor-vcp_contraction-d10-h20`),
byte-exact verdict values (holdout/p), a full selector-mismatch matrix (factor/decile/horizon/direction/
slice_kind — L389-402), empty/null/undefined fail-safe (L405-413), matched-but-non-PASS ma_stack →
"Not yet proven" (L378-386), and collision-free anchors (L416-435). No loose "something returned" assertions.

**T2 — OBSERVATION: J-02 verified in the canonical lane (QA functional TC-07 "SKIP" was redundant).**
The QA functional table marked TC-07 (J-02 proof drill-down) SKIP deferring to the dev handoff, which would
have been a soft verification gap. However the **canonical** browser-qa lane covers it directly: UT-16
(`reports/phase-goal-mcp-loop-iter-8-ui-test-results.md` L37/L178-186) opens `/stocks/MU` → "Why proven?" and
confirms "PASS · holdout edge +6.36%", "+6.36% vs SPY (benchmark control)", "leadership_score · registered
2026-06-30" — PASS. The stock-detail path is also provably untouched (zero diff; `resolveEvidenceStatus`/
`proofFieldsFor` unchanged; `proven_signals` unit-asserted to stay `{leadership_score}`), so J-02 cannot have
regressed. No gap remains.

---

## 3. Domain Assessment

The core domain invariant — **proven-ness flows solely from a PASS certified-claim and is re-displayed
verbatim, never recomputed** — is fully preserved across the new surface. The signal-less plain-factor cohort
is correctly excluded from `proven_signals` (so no `/stocks` inline score badge lights), while a new pure
cohort-selector matcher reads the SAME `GET /api/evidence` payload to mark the factor lab. The matcher is
fail-safe at every branch (no claims / fetch error / matched-but-FAIL → "Not yet proven", no link), which the
canonical UT-11 confirms live (all 11 badges fall back to "Not yet proven" on a forced fetch failure, no
crash). Determinism and no-lookahead are untouched (zero engine/referee/`api/evidence`-shape diff). The
honest-failure posture is intact and visible: the rejected `ma_stack` cohort is audit-listed as FAIL and
reads "Not yet proven" on both surfaces (UT-09/UT-10/UT-12). Architecture remains local-first and minimal —
one pure helper module, one new read-only table column, one row-anchor, one test; no new endpoint, no new
page, no nav change. The implementation is correct, not merely rendering.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issue was found; all findings are OBSERVATION-level or a non-gating GAP and are documented above, per auditor scope. |

---

## 5. Recommended Next Step

**Proceed.** J-06 is genuinely delivered and all six Must-have journeys (J-01…J-06) are green in the canonical
browser-QA lane with byte-accurate displayed numbers; the goal-evaluator can re-assess GOAL_ACHIEVED.

Optional, non-blocking carry-forward (do not gate this iteration):
- **G1 (GAP, non-gating):** the demo-narrator script (`reports/phase-goal-mcp-loop-iter-8-demo.json`) was
  authored correctly with `"new": true` flags + plain-language narration + vcp_contraction content, but the
  Playwright runner SKIPPED screenshot capture because Playwright (Python) is not installed in this
  environment (`...-demo-results.md`: "Demo Verdict: SKIPPED"). Showcase only — install Playwright to render
  the gallery when convenient.
- **F2/F3 (OBSERVATION):** if a future iteration touches `_labs.tsx`, add `e.stopPropagation()` to the passive
  "Not yet proven" chip (or make the whole evidence cell swallow the click) for click consistency, and drop
  the unused `cohortEvidenceAnchor` import.
