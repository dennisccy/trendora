# goal-mcp-loop-iter-28 Dev Handoff

**Phase:** goal-mcp-loop-iter-28
**Date:** 2026-07-12
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing.** This is a deliberate verify-only / plateau-assessment iteration, per the iter spec's IN
SCOPE section ("None. No source change.") and the coordinator note. No product code, no data model, no
UI, and — critically — no `## Evidence Claim` was authored, submitted, or promoted. The work product is
the verification below plus the documented plateau finding for the evaluator.

### Verification performed

1. **Product-source / ledger byte-identity.** Confirmed via
   `git diff HEAD --stat -- apps/backend/app apps/frontend config.yaml apps/backend/data/seed
   runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl`
   → **empty output** (no changes) both before and after this pass. `apps/backend/app/**`,
   `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, `certified-claims.jsonl`, and
   `staging-ledger.jsonl` are all byte-identical to HEAD.
2. **No Evidence Claim registered.** Confirmed the iter spec (`docs/phases/goal-mcp-loop-iter-28.md`)
   contains no `## Evidence Claim` block (grep-verifiable — the spec explicitly states this is
   deliberate/load-bearing) and this handoff submits none. The post-decompose gate therefore passes
   automatically and the canonical Bonferroni divisor stays at **8**.
3. **Targeted frozen-golden ledger tests** (the only tests this iteration runs — NOT the full suite,
   which is ~10-11h at the 30-year basis and would fork-lock the host):

   ```
   apps/backend/.venv/bin/python -m pytest \
     tests/test_evidence.py::test_canonical_ledger_frozen_golden \
     tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery \
     -v
   ```

   Result: **2 passed in 0.23s**. Both pin the ledgers byte-for-byte: 7 canonical entries (strict
   Bonferroni divisors 1..7, register_date 2026-07-03, all FAIL, `proven_signals == {}`) and 7 staging
   entries (the §4.1 four single-factor + §4.2 three combination pre-registered candidates, LORD++
   economy, register_date 2026-07-03, all FAIL, zero rejections, strictly-decreasing `required_p`
   sequence). Neither test needed edits — they still pass unedited against the committed ledgers,
   confirming no accidental drift.

## Plateau finding (recorded referee evidence, read not recomputed)

The complete pre-registered candidate set (`project-extensions/proposer-guidance.md` §4.1 four
multi-horizon singles + §4.2 three combinations) has already been run through the referee on the 30-year
basis, and **every member FAILS** on both ledgers. Quoted verbatim from the two ledgers on disk:

**Canonical `certified-claims.jsonl`** — 7 entries, register_date 2026-07-03, seed 20240601, strict
Bonferroni divisors 1..7 (current canonical divisor **8**, `required_p = 0.05/8 = 0.00625`), **all FAIL**:

| # | cohort | horizon | holdout_edge | p_value | note |
|---|--------|---------|--------------|---------|------|
| 1 | leadership_score | 20 | −0.000314 | 0.535 | wrong direction |
| 2 | event-study Breakout-watch / Risk-on | 20 | −0.006842 | 0.946 | wrong direction |
| 3 | ma_stack | 20 | +0.002062 | 0.277 | right direction, far from bar (closed FAIL since iter-8) |
| 4 | vcp_contraction | 20 | −0.003773 | 0.960 | wrong direction |
| 5 | vcp_contraction | 60 | −0.016364 | 0.9995 | wrong direction |
| 6 | combination rs_spy_3m×high_proximity | 20 | +8.03e-05 | 0.494 | ~zero edge |
| 7 | rs_spy_3m | 60 | −0.014155 | 0.905 | wrong direction |

**Staging `staging-ledger.jsonl`** — 7 entries (the complete §4.1 + §4.2 pre-registered set), online-FDR
(LORD++) economy, register_date 2026-07-03, **all FAIL**, zero discoveries (`rejection_offsets == []`),
strictly-decreasing `required_p` across all 7 trials (wealth never replenished):

| # | candidate | holdout_edge | p_value | required_p (LORD++) |
|---|-----------|--------------|---------|----------------------|
| 1 | vcp_contraction h10 | −0.00266 | 0.8921 | 0.010937 |
| 2 | vcp_contraction h60 | −0.01636 | 0.9995 | 0.003608 |
| 3 | rs_spy_3m h60 | −0.01416 | 0.9045 | 0.001886 |
| 4 | leadership_score h60 | −0.00388 | 0.6587 | 0.001190 |
| 5 | combo rs_spy_3m×atr_pct | −0.00416 | 0.9200 | 0.000833 |
| 6 | combo leadership_score×atr_pct | −0.00442 | 0.9215 | 0.000622 |
| 7 | combo rs_spy_3m×high_proximity | +8.03e-05 | 0.4943 | 0.000486 |

Six of seven staging candidates are wrong-direction (negative holdout edge); the one non-negative
(#7, shared with canonical #6) is essentially zero (+8.03e-05) and three orders of magnitude off its
required_p.

**Conclusion:** the complete §4.1/§4.2 pre-registered candidate set is empirically exhausted on the
30-year basis — no member of either ledger clears its bar, and re-submitting any of them would be a
closed hypothesis (iter-8/iter-10/iter-12 lesson) that only tightens the divisor further for no possible
gain. Per `proposer-guidance.md` §4.2's named escape valve, the only remaining unblock for J-02/J-06/
J-07/J-08/J-09 is a **human** revision of the pre-registered candidate registry (`docs/goal.md` §4.1/§4.2
or `proposer-guidance.md`) — not an action this developer pass or any autonomous agent may take. This
finding is handed to the evaluator to weigh the STALLED-with-menu / goal.md-amendment / CONTINUE options
enumerated in the iter spec's NOTES section; this handoff does not choose the verdict.

## Files Changed

None. `git diff HEAD` is empty on all product source (`apps/backend/app/**`, `apps/frontend/**`,
`config.yaml`, `apps/backend/data/seed/**`) and on both evidence ledgers
(`runs/goal-session-mcp-loop/state/certified-claims.jsonl`,
`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`). No files were written or edited by this
developer pass other than this handoff and `runs/goal-mcp-loop-iter-28/status.json`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py::test_canonical_ledger_frozen_golden tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery -v`

Result: **2 passed, 0 failed** (0.23s). This is the DoD-named targeted invocation only — the full suite
(~10-11h at this data basis, per the trendora-30y-test-suite-slow-not-product session note) was
intentionally NOT run.

No dev/frontend services were started for this pass (no source changed, nothing to smoke-test at the
service level); the DoD-required deterministic golden-script replay of J-01/J-03/J-04/J-05/J-11/J-10/J-13
against the live `/api/evidence` all-FAIL payload is the browser-qa lane's job downstream, not this
developer pass's — this handoff's scope (per the coordinator note) is the targeted ledger tests, the
byte-identity confirmation, and the plateau documentation.

## Known Issues

- None introduced by this pass — zero code touched.
- Carried forward from iter-27 and explicitly OUT OF SCOPE here (do not bundle): B1
  `IndicatorsCfg._validate` `max_needed` guard hole; T1/F1 browser-qa backend-lifecycle permission;
  `rm -rf .pytest-tmp-iter27/` scratch cleanup.
- The five target journeys (J-02, J-06, J-07, J-08, J-09) remain sanctioned-partial. This iteration
  confirms — it does not and cannot change — that outcome; see "Plateau finding" above.
