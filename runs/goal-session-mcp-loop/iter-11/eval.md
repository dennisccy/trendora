# Iteration 11 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-11 surfaced **J-07** end-to-end: the referee-certified `vcp_contraction` D10 @ **h60** signal-less edge was promoted to the canonical ledger (5th entry, PASS, +8.91% holdout, p=0.0004998, Bonferroni divisor 5) and rendered as a per-horizon "Proven" badge on `/research/factor-lab` deep-linking to a new `/evidence` row, with h1/h5/h10 honestly reading "Not yet proven". J-07 flips `unknown -> passing` (progress), but **J-08** (multi-factor combination) remains `unknown`/unbuilt — explicitly out of scope this iteration — so the goal is not yet achieved. No regression, no anti-goal violation, coherence COHERENCE-PASS.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | `proven_signals` pinned `{leadership_score}` (frozen-golden test on real ledger); zero `/stocks` code change; UT-11 leadership_score still "Proven" |
| J-02 | passing | passing | certified-claims.jsonl L1 git-unmodified; no router/engine/evidence.py change (byte-identity path) |
| J-03 | passing | passing | signal-less h60 claim backs factor lab only; UT-07 (h1/h5/h10 dark), UT-08 (ma_stack FAIL 5/5 "Not yet proven") — `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png` |
| J-04 | passing | passing | Breakout-watch "Regime: Risk-on" PASS +6.12% visually confirmed — `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png` |
| J-05 | passing | passing | 5 rows; prior 4 visually unchanged + my `git diff` shows exactly 1 appended ledger line — `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png` |
| J-06 | passing | passing | vcp h20 row PASS +3.33% visually confirmed; UT-10 h20 chip still "Proven"; UT-13 h20 subtitle no "60-day" — `reports/qa/goal-mcp-loop-iter-11-evidence/UT-12-UT-13-evidence-rows.png` |
| J-07 | unknown | **passing** (newly) | DOM UT-04 (h60 chip data-proven=true, href `/evidence#factor-vcp_contraction-d10-h60`), UT-05 (h60 row all fields), UT-06 (click nav), UT-07 (h1/h5/h10 not proven) + byte-exact ledger L5 + green unit tests — `reports/qa/goal-mcp-loop-iter-11-evidence/UT-04-UT-07-vcp-chips.png` |
| J-08 | unknown | unknown (unbuilt) | Out of scope this iter; deferred to iter-12+ per goal.md Part B sequencing |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| "Proven" only if backed by passing certified-claim | OK | h60 "Proven" deep-links to a real PASS L5; h1/h5/h10 + ma_stack FAIL render "Not yet proven" (UT-07/UT-08) |
| Decision-quality only (no return/price/buy-sell) | OK | grep of frontend+ledger diff for buy/sell/price-target/predict/guarantee = clean; row shows only factual ledger fields |
| Displayed numbers correct (match engine) | OK | h60 +8.91% / p=0.0004998 byte-match certified-claims.jsonl L5 (my independent `git diff`); no UI recompute |
| No overfit edges (referee-certified) | OK | Gate certified PASS via sealed holdout + SPY control + Bonferroni divisor 5; raw p clears required_p=0.01 with margin |
| Preserve determinism / no-lookahead | OK | Zero `apps/backend/app/**` diff; h60 verdict is the gate's, reproduced verbatim (in-sample<=as-of, holdout>as-of) |
| No iteration ships without passing referee verdict | OK | Post-decompose gate certified the h60 claim PASS before build (fail-closed) |
| No hard-coded credentials/keys/tokens | OK | Secret scan of the diff = clean |

## Next-Step Recommendation

**iter-12 (FULL) — surface J-08** (the sole remaining Must-have journey). Promote ONE PRE-REGISTERED 2-factor combination from the config-backed candidate set (never an ad-hoc data-mined cohort) via an explicit `"ledger":"canonical"` `## Evidence Claim`. It now faces **Bonferroni divisor 6 (required_p ~= 0.00833)** after iter-11's canonical write tightened the bar 5->6 — promote only a candidate whose recorded raw p clears 0.00833 with margin. Surface the new combination row on `/evidence` + a "Proven" badge on `/research/factor-combination` (uncertified combinations read "Not yet proven"); keep it signal-less so J-01/J-02/J-03 stay unaffected. FULL depth because it ships a new referee-gated canonical claim + a new public-surface badge (the auditor-grade high-stakes write, mirroring iter-8/iter-11).

**Browser-QA hard requirement for iter-12:** actually scroll each asserted badge/row into the viewport and capture DISTINCT screenshots — do NOT relabel a single full-page capture across many UT ids (see Halt/notes below; the iter-3 lesson recurred this iteration).

GOAL_ACHIEVED becomes reachable the moment J-08 lands browser-verified with J-01..J-07 non-regressed.

## Skeptical Finding (non-blocking, evidence hygiene)

`md5sum` on the 11 evidence PNGs collapses them to **3 distinct images**: one factor-lab-top (UT-01/03/04/07/10/14 all share two hashes), one evidence-page-top (UT-02/05/06/12), and one backend-unavailable (UT-09). None of the pixel captures shows the vcp_contraction row, the h60 "Proven" chip, the h60 `/evidence` row, or the vcp h20 chip **scrolled into the viewport** — despite the spec citing the iter-3 lesson verbatim ("scroll each asserted badge into the viewport before capture"). The auditor's claim of "scrolled-into-frame screenshots" is overstated. This does **not** flip J-07: its assertions are DOM/JS-eval based against a live `:3255/:8255` stack and converge with a byte-exact `git diff` on `certified-claims.jsonl` (L5) + green `factor-lab-evidence.test.ts`/`evidence.test.ts` + the dev's live curl. The gap is documentation hygiene, not a functional failure, and is captured as an iter-12 browser-qa requirement.

## Halt Justification

Not halting. This is a `CONTINUE`: exactly one Must-have journey newly passed (J-07), one remains unbuilt by design (J-08), and a concrete, high-confidence next step is identified. GOAL_ACHIEVED is blocked solely by J-08's `unknown` status (rules forbid GOAL_ACHIEVED with any unknown journey); no regression or critical anti-goal violation exists to force a REGRESSION halt, and there is no stall (real load-bearing progress + a specific next target).
