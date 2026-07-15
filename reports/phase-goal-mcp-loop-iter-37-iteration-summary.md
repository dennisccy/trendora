# Iteration Summary — goal-mcp-loop-iter-37

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-15
**Iteration:** 37

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" label on every score, open a fully auditable record behind any tested idea, and view up to thirty years of price history plus benchmark and macro context, each clearly sourced. You can browse every idea the system has planned, tested, or rejected, see how much of its statistical testing budget has been used, and rely on one shared trust banner shown on every page that also watches for live data silently drifting from validated history and for whether the testing system's own checker is trustworthy.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team spent this round double-checking that everything already built (all 22 finished areas) still works correctly, and gave two trust checks — the evidence audit trail and the "nothing proven has quietly gone stale" check — a fresh, dedicated confirmation to close out some unfinished paperwork left over from last round.

**What's next:** Next we'll add a view that shows how concentrated a user's watchlist really is, flagging when several picks are secretly all betting on the same thing.

## Headline

Lean closeout: zero-code regression replay re-verifies all 20 journeys, closes iter-36's replay gap

## Direction

**Signal:** holding
**Why:** iter-37 was a zero-code verification pass that formally re-confirmed all 20 built journeys via deterministic replay (18/18 PASS) plus a dedicated live browser walk on J-05 and J-11 — the two rows iter-36's CLOSURE-FAIL had left unverified — closing that gap with no journey changing status. The last five iterations have steadily added journeys (J-20 at iter-33, J-21 at iter-35, J-22 at iter-36) with zero regressions, so the project is on a healthy trajectory; the only work left is the three unbuilt risk-analytics journeys (J-23/J-24/J-25), starting with J-23 next.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-20 (iter-33), J-21 (iter-35), J-22 (iter-36)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none new (the iter-24 and iter-26 critical anti-goal #8 entries remain resolved)
- Iters with no journey state change: 2 of last 5 (iter-34, iter-37)

**Latest evaluator reasoning:** iter-37 is the lean, verification-only closeout the iter-36 CONTINUE asked for: it ran the deterministic golden-script regression replay that a FULL iteration structurally skips (`run-phase.sh` has no replay lane — only `goal-iter-lean.sh` does), formally re-verifying all 20 built, golden-scripted journeys with zero product change and closing the iter-36 CLOSURE-FAIL replay gap. The replay produced `regression-replay-results.md` (the artifact iter-36's full path never wrote): 18/18 deterministic PASS over the Required-still-passing set — folding in J-21.json (iter-35) and J-22.json (iter-36) for the first time — while the two closure-named Targets J-05 and J-11 got a dedicated LLM browser-qa live walk plus a linted/replayed golden self-check (merged results 20/20 PASS). No journey regressed, coherence is COHERENCE-PASS, and all 8 anti-goals hold; GOAL_ACHIEVED is not reachable because J-23/J-24/J-25 remain unbuilt.

## What was done

- Ran the deterministic golden-script regression replay (`demo_runner.py --mode verify`) across all 20 built journeys, producing `regression-replay-results.md` (18/18 PASS) — the artifact iter-36 never wrote
- Folded in the two accumulated goldens, J-21.json (iter-35) and J-22.json (iter-36), into the deterministic replay lane for the first time
- Gave the two iter-36 closure-named journeys — J-05 (evidence ledger audit) and J-11 (no-stale-edge check) — a dedicated live browser walk plus a golden self-check, formally closing that gap
- Confirmed zero product/ledger diff (git diff empty on backend, frontend, config, seed data, and both evidence ledgers — still 7/7 FAIL, divisor stays 8) and re-ran two targeted frozen-ledger tests (2/2 passed)
- Verified a clean prod-mode boot from a forced-cold frontend rebuild; 16 pages spot-checked all HTTP 200, backend preflight read GO
- Merged replay and browser-qa results into `ui-test-results.md`: 20/20 journeys PASS overall
- Verified 2 target journey(s) pass browser QA (J-05, J-11)

## What's left

- J-23 — watchlist concentration/correlation X-ray (backlog B-204) — unbuilt; the next FULL iteration's target
- J-24 — per-stock risk-budget card (backlog B-201) — unbuilt; deferred until after J-23
- J-25 — drawdown/dry-spell expectations panel (backlog B-205) — unbuilt; deferred until after J-23
- Systemic framework gap: a FULL iteration still has no deterministic-replay lane (`run-phase.sh` lacks one) — has caused CLOSURE-FAIL twice (iter-33, iter-36); a durable fix (add the replay lane to the full path) is recorded but not yet applied
- Minor non-blocking carry-forwards from iter-36 (audit findings B1/B2/F1, stale wording in dev-handoff/what-to-click/ui-test-plan) — explicitly deferred, not bundled into this pass

## Next step

iter-38 = FULL J-23 (backlog B-204 watchlist concentration X-ray — pairwise correlation view, cluster groupings, sector/theme concentration, headline "effective independent bets" with its window stated; the ENB helper is the same module the evidence correlation audit will use, so it stays single-source; NA over fabrication for insufficient overlap; no Evidence Claim, divisor stays 8). FULL because it ships a new served surface + endpoint needing the audit/ux-regression/closure guards — read the binding B-204 card in `docs/improvement-backlog.md` before planning. Carry the systemic flag: a FULL iteration re-creates the deterministic-replay gap (`run-phase.sh` still has no replay lane — it has CLOSURE-FAILed on this twice, iter-33 and iter-36), so iter-38 must either run the closure one-liner replay inline or be followed by another lean verify pass (as iter-34 and iter-37 were). Three journeys remain (J-23 → J-24/J-25, the risk-analytics cluster, one risky journey per iteration); once they land, GOAL_ACHIEVED becomes reachable.

## Assumptions made

- iter-38 · goal-decomposer — Ambiguity: J-23's acceptance implies the future evidence-correlation-audit's ENB helper already exists, but that audit (backlog B-104) is unbuilt and no ENB/correlation helper exists anywhere yet. We chose: Build the one canonical ENB/correlation helper (`app.engine.concentration`) in iter-38 as the single source; the future B-104 audit will import the same helper rather than duplicating it. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: the DoD required J-01/J-03/J-05/J-11/J-17/J-18/J-19/J-20 to be live-re-verified, but neither the browser-qa lane nor a golden replay actually covered J-05/J-11 (QA's rows were unevidenced conclusions); open whether to carry them at last-good passing or mark them re-verified. We chose: marked J-05 and J-11 re-verified passing at iter-36 on frames the evaluator personally opened, but left the dedicated per-journey golden replay formally open as the mandated next lean-closeout step (which iter-37 then performed). Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL, and the session's usual rule withholds "passing" from a target whose canonical evidence is incomplete — but J-22's own evidence was clean and complete; the CLOSURE-FAIL was about a different DoD line (other journeys' replay). Open whether J-22 should be "passing" or "partial". We chose: scored J-22 passing — the closure auditor itself exempted J-22's own deliverable from the finding, so marking it partial would misattribute someone else's gap to it; the overall verdict stayed CONTINUE (not GOAL_ACHIEVED) to honor the gap at the session level. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: J-22's acceptance could be read as requiring a live 200-trial run in the QA lane, or a bounded/offline seeded run whose persisted artifact the panel and browser-qa read. We chose: a two-halves decomposition — a fast seeded test proves the job-to-artifact half, and browser-qa reads the persisted artifact for the UI half; the heavy 200-trial battery runs offline only (anti-goal-#8 memory discipline), never live in the browser lane. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: J-21 and J-16's acceptance reads as one end-to-end "click Fetch and watch it update" observation, but browser-qa actually verified it via a fetch-to-artifact integration test plus a separate artifact-to-UI direct-injection check — no single browser click covered the whole path. We chose: accepted the two-halves decomposition as sufficient (the artifact is the single-source seam both readers share), with a live-Fetch-UI spot check recommended as a future refinement, not a gate. Reversible: yes
- iter-35 · goal-decomposer — Ambiguity: B-304's card describes three post-fetch checks, but J-21's actual journey acceptance only exercises the overlap check plus the readiness effect; the third check's B-113 sentinel dependency doesn't exist yet. We chose: scoped iter-35 to the overlap comparator + drift artifact + preflight component only, deferring the distribution-envelope and B-113-dependent seam scan since neither is required by J-21's stated acceptance. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: J-20 was the named target to "re-confirm passing," but only its quiet GO state was re-induced live this pass — the loud DEGRADED/NO-GO states were not (a tool-permission boundary) — leaving open whether a GO-only re-confirmation counts. We chose: scored J-20 passing/re-confirmed anyway, since it was already fully verified (all three states) at iter-33 and the product code was byte-identical since then — no regression mechanism existed to justify re-testing the loud states again. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL, and this session usually withholds "passing" from a target in that situation — but here the CLOSURE-FAIL was about six OTHER required journeys' missing replay, not J-20's own (complete, clean) evidence. Open whether J-20 is "passing" or "partial". We chose: scored J-20 passing, since marking it partial would misattribute an unrelated replay gap to J-20's own fully-verified evidence; the gap was instead recorded at the overall-verdict level. Reversible: yes
- iter-33 · goal-decomposer — Ambiguity: B-301's "data freshness vs expectation" is underspecified for an offline app running on a frozen seed — a real wall-clock "now" would make the healthy GO state impossible and break determinism. We chose: anchor freshness to a deterministic seed-derived reference date (never wall-clock time), counted in trading days, with the stale/degraded test states induced only via a controlled config override, never by touching the committed seed data. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: J-11 (no displayed "Proven" edge should ever go stale) was in the required-still-passing set but got no dedicated replay or browser case that iteration; open whether it needs its own dedicated re-verification each iteration or whether corroborating evidence suffices. We chose: scored J-11 passing on byte-identity plus corroboration (a 0-PASS ledger trivially satisfies "no stale Proven edge"), rather than downgrading it to unknown; recommended a dedicated J-11 replay for a future iteration, which iter-37 then delivered. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-37.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-37-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-37-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-37-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-37/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
