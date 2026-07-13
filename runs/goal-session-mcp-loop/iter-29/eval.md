# Iteration 29 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-29 was the verify-only, zero-code pass the iter-28 STALLED menu asked for: the owner acted at
the plateau (goal.md HEAD `eb19cee`, docs-only) by re-scoping J-02/J-06/J-07/J-08/J-09 to
**outcome-neutral** acceptance (each passes in EITHER the "Proven" or the honest "Not yet proven"
state, so long as the surfacing is honest and correct) and pulling nine backlog cards into new
Must-have journeys J-17..J-25. This iteration banks the five flips cleanly — all five are now
browser-verified `passing` against the CURRENT goal text with the ledger's all-FAIL numbers
byte-matched — re-establishing a fully-green J-01..J-16 baseline. GOAL_ACHIEVED is NOT reachable:
goal.md now carries 25 Must-have journeys and J-17..J-25 are unbuilt (`unknown`), so the loop
continues onto the new-feature work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-01-verify.png |
| J-02 | partial | **passing** | reports/qa/goal-mcp-loop-iter-29-evidence/J-02-stock-detail-badges.png |
| J-03 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-03-verify.png |
| J-04 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-04-verify.png |
| J-05 | passing | passing (replay + spot-check) | reports/qa/goal-mcp-loop-iter-29-evidence/J-05-verify.png |
| J-06 | partial | **passing** | reports/qa/goal-mcp-loop-iter-29-evidence/J-06-evidence-row-vcp-h20.png |
| J-07 | partial | **passing** | reports/qa/goal-mcp-loop-iter-29-evidence/J-06-J-07-J-09-factor-lab-fullpage.png |
| J-08 | partial | **passing** | reports/qa/goal-mcp-loop-iter-29-evidence/J-08-factor-combination-lab.png |
| J-09 | partial | **passing** | reports/qa/goal-mcp-loop-iter-29-evidence/J-09-factor-lab-rs-spy-3m-row.png |
| J-10 | passing | passing (replay + corroborated) | reports/qa/goal-mcp-loop-iter-29-evidence/J-10-verify.png |
| J-11 | passing | passing (replay + ledger on disk) | reports/qa/goal-mcp-loop-iter-29-evidence/J-11-verify.png |
| J-12 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-12-verify.png |
| J-13 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-13-verify.png |
| J-14 | passing | passing (replay) | reports/qa/goal-mcp-loop-iter-29-evidence/J-14-verify.png |
| J-15 | passing | passing (byte-identity, evaluator-confirmed zero diff) | git diff HEAD --stat config.yaml apps/** = empty |
| J-16 | passing | passing (byte-identity, evaluator-confirmed zero diff) | git diff HEAD --stat config.py/prices.py/scoring.py/warmup.py = empty |
| J-17..J-25 | (new) | **unknown** (unbuilt, out of scope) | goal.md HEAD eb19cee; deferred to future FULL iters |

Independently verified (not trusted from handoffs):
- **Zero product diff.** `git diff HEAD --stat` AND `git diff 6492189a..` (the iteration snapshot)
  are both empty on `apps/**`, `config.yaml`, `apps/backend/data/seed`, and both `*-ledger.jsonl`.
  HEAD (`eb19cee`) touches exactly one file — `docs/goal.md` (286+/99-). No regression mechanism
  exists for any stable journey. `iter-diff.md` reads "(no changes)".
- **Ledger byte-match (anti-goal #3).** Read `certified-claims.jsonl` on disk: 7 rows, 0 PASS,
  7 FAIL. The four DoD-named rows byte-match: vcp_contraction D10 h20 = −0.0037732 (−0.38%),
  vcp D10 h60 = −0.016364 (−1.64%), rs_spy_3m×high_proximity composite h20 = +8.03e-05 (+0.01%),
  rs_spy_3m D10 h60 = −0.014155 (−1.42%); divisors 4/5/6/7; register 2026-07-03.
- **The five target screenshots are md5-distinct** and each shows its acceptance state (see
  Anti-goal Check / notes). The nine required-still-passing journeys replayed PASS via golden
  script; several `-verify.png` frames share md5 (e.g. J-04/05/06/07/08/09-verify all end on the
  `/evidence` top viewport) — a benign shared-endpoint capture artifact, NOT a broken frame: the
  evaluator opened one (J-05-verify.png) and confirmed a real `/evidence` page with byte-matching
  numbers; replay PASS is assertion-driven, not screenshot-driven.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 Nothing "Proven" without a passing certified-claim | OK | 0 PASS in both ledgers (on disk). Evaluator opened the factor-lab fullpage: all 11 factors "Not yet proven" at every horizon; J-08 combination "Not yet proven"; J-02 detail shows no fabricated proof panel. Browser-qa page-wide grep: 0 `data-proven="true"` / `>Proven<`. |
| #2 Decision-quality only (no buy/sell/returns/orders) | OK | "Research-only · decision support · no orders" header on every opened frame; combination lab framed "Descriptive, not predictive". No new copy (zero diff). |
| #3 Displayed numbers correct (match engine) | OK | Four DoD rows byte-match `certified-claims.jsonl` on disk (see above). Retired values render nowhere (grep 21.34/0.0004998 = 0; the lone "6.36" hit is a false-positive substring inside p_value 0.9045477261369316). |
| #4 No overfit edges shown as proven | OK | No edge is shown proven at all (all-FAIL ledger). |
| #5 Determinism + no-lookahead | OK | Zero engine diff (scoring/referee/evidence/ledger/forward_walk byte-identical). |
| #6 No iteration ships evidence claims lacking a passing referee verdict | OK | No `## Evidence Claim` in the iter spec (grep 0); canonical Bonferroni divisor stays 8; both ledgers byte-unchanged. |
| #7 No hard-coded credentials/keys/tokens | OK | `scan-report.md` CLEAN — no secret/dependency/license findings on added lines (and there are no added product lines). |
| #8 Resilience to data-shape/scale change (no crash/OOM) | OK | Zero code diff ⇒ no new data-path/crash mechanism. Both prior #8 violations (iter-24, iter-26) remain `resolved=true`. |

Deterministic scan: CLEAN. Coherence: **COHERENCE-PASS** (independently re-derived zero product
diff; both ledgers 7/7 FAIL; no new Data Contract row or route; the only tracked change is a 2-line
additive blueprint clarification). No structural veto.

## Next-Step Recommendation

iter-30 (**FULL**). The five re-scoped "old-scope" journeys are banked; GOAL_ACHIEVED now depends
solely on the nine new backlog-derived journeys **J-17..J-25**. Take exactly ONE risky new surface
per iteration (rule 5 forbids bundling risky work) — each ships a new page/endpoint/value and needs
the full audit / ux-regression / closure guards, and each will likely need a nav-skeleton edit +
`blueprint.reapproval-requested`. Per the iter-29 spec's recommended sequencing, start with the
**governance keystone J-18** (registry-enforcement gate, backlog card B-901 — the pre-registration
gate that J-19 reads), then J-17 (budget panel, B-903) and J-19 (graveyard, B-902); then daily-ops
J-20 (B-301) / J-21 (B-304); certifier-audit J-22 (B-102); risk-analytics J-24 (B-201) / J-25
(B-205) / J-23 (B-204). Read the binding backlog card in `docs/improvement-backlog.md` (its
What / How / Config surface / ★ Canonical value / ★ Do NOT touch / Traps) before planning each — do
NOT plan from the goal.md one-liner alone. Each of J-17..J-25 carries **NO Evidence Claim** (no
proven-language), so none can collide with the canonical closure; the divisor stays 8. Do NOT
re-submit any closed FAIL to the referee (tightens the divisor 8→9 for no gain); new edge hunts
require an owner-registered candidate only.

Non-blocking carry-forwards (do NOT bundle): the browser-qa `-verify.png` replay frames dedup across
same-endpoint journeys (consider element-clip captures so each journey's frame is independently
distinct); B1 `IndicatorsCfg._validate` `max_needed` guard; T1/F1 browser-qa backend-lifecycle
permission; `rm -rf .pytest-tmp-iter27/` scratch.

## Halt Justification (if halting)

N/A — not halting. CONTINUE. Progress was made (five journeys `partial` → `passing`); no journey
regressed; no unresolved anti-goal; coherence is COHERENCE-PASS (no consolidation debt); and
tractable next work exists (J-17..J-25 are concretely specced backlog cards). GOAL_ACHIEVED is
withheld only because the nine new Must-have journeys J-17..J-25 are unbuilt (`unknown`) — per the
rule that no Must-have journey may be `unknown` at GOAL_ACHIEVED.
