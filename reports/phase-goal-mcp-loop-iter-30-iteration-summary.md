# Iteration Summary — goal-mcp-loop-iter-30

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-13
**Iteration:** 30

## In plain words

**What you can do now:** Browse a full leaderboard of hundreds of companies with an honest "proven" or "not yet proven" label on every score, open an auditable evidence ledger showing exactly how each trading idea performed in real testing, and view up to thirty years of price history for any stock. The dashboard shows three decades of major-index history plus a volatility gauge and a rate indicator, each labeled by source, and the Data Manager page shows a color-coded data-coverage calendar for the whole company list — the heaviest data-refresh job now runs reliably without crashing. You can now also browse the complete history of every trading idea the system has ever registered or tested — what it claimed, why, when, and its current status — all in one place.

**What changed this time:** This round adds a new page where you can see every hypothesis the system has ever tried, including early ones and later formally confirmed ones. Just as importantly, though invisible to you as a user, the system now refuses to test any brand-new idea going forward unless it was written down and registered ahead of time — a safeguard against quietly cherry-picking results after the fact.

**What's next:** Next, the team plans to make the statistical "testing budget" visible before it's spent, and build a browsable record of every idea that didn't pan out, so nobody accidentally retries a dead end.

## Headline

Shipped the pre-registration registry + gate enforcement (J-18 passes)

## Direction

**Signal:** improving
**Why:** iter-30 shipped J-18 (pre-registration registry + gate enforcement) cleanly: browser-QA 10/10 (including the DoD-named discoverability + 11-row check), 30/30 backend gate-fixture tests, review PASS, audit PASS with zero fixes required, and closure CLOSURE-PASS with no blocking issues. All required-still-passing journeys (J-01/02/03/05/06/07/08/09/11) were independently confirmed unaffected — both evidence ledgers and `GET /api/evidence` stay byte-identical, and the Bonferroni divisor stays 8. J-17 and J-19..J-25 remain unbuilt, so GOAL_ACHIEVED still depends on those eight; note that the formal goal-evaluator record for iter-30 had not been written at summary time, so this verdict and direction are carried from the closure/QA/audit/review chain — the strongest sources available.

**Trend (last 5 iters):**
- Newly passing this iter: J-18
- Newly passing in last 5 iters total: J-02, J-06, J-07, J-08, J-09, J-16, J-18
- Regressions in last 5 iters: J-16 (iter-26; recovered iter-27)
- Anti-goal violations in last 5 iters: 1 critical (anti-goal #8, iter-26; resolved iter-27)
- Iters with no journey state change: 1 of last 5 (iter-28)

**Latest evaluator reasoning:** iter-29 is the lean verify-only pass the iter-28 STALLED menu asked for, and it banked cleanly. The owner acted at the plateau (goal.md HEAD eb19cee, docs-only, git-verified: 286+/99- on exactly one file) by re-scoping J-02/06/07/08/09 to outcome-neutral acceptance (passes in EITHER "Proven" or the honest "Not yet proven" state) and pulling 9 backlog cards into J-17..J-25. NOT GOAL_ACHIEVED (goal.md now has 25 Must-have journeys; J-17..J-25 are unbuilt/unknown — no Must-have may be unknown at achievement).

## What was done

- Shipped `/research/registry` — a read-only page listing all 11 backfilled hypotheses (selectors, rationale, registration date, source, status), reachable in 1 click from the Research hub's new "Governance & process" section.
- Added a machine-enforced pre-registration gate in `verify_claim.py`: any future Evidence Claim must exactly match a registry row or it is refused before any statistical test runs — no fuzzy matching.
- Backfilled the registry from both evidence ledgers plus the pre-registered candidate list: 14 raw entries deduplicate to 11 distinct hypotheses (3 exact cross-ledger duplicates), independently verified programmatically by the developer, reviewer, and auditor.
- Flipped `evidence.registry.enforce` to true only after backfill completeness was verified — the sequencing the spec required.
- Confirmed zero impact on existing surfaces: both evidence ledgers, the referee, and `GET /api/evidence` are byte-identical before/after; the Bonferroni divisor stays 8.
- Verified J-18 passes browser QA (10/10 UI tests, including the DoD-named discoverability + 11-row check) plus 30/30 backend gate-fixture tests (registered / unregistered / near-miss / enforcement-off / missing-file).

## What's left

- Journeys J-17, J-19, J-20, J-21, J-22, J-23, J-24, J-25 (statistical-budget visibility, dead-hypothesis graveyard, daily preflight/go-no-go verdict, live-data drift guard, referee self-calibration audit, watchlist concentration X-ray, per-stock risk-budget card, drawdown/dry-spell expectations) remain unbuilt/unknown — GOAL_ACHIEVED now depends solely on these eight.
- The gate's enforcement (and the `evidence.registry.enforce` flag) has no UI and never will, by design — it only affects future iterations that submit a new Evidence Claim.
- The registry is intentionally read-only — no UI exists to add, edit, or withdraw a registration; new rows can only be appended by the gate/tooling.
- The registry only knows the 11 hypotheses tested so far; any future hypothesis must be registered before it can be certified.
- Non-blocking hardening flagged by the audit: `registry.py`'s `_CLAIM_SELECTOR_KEYS` is a hand-synced copy of `tools.py`'s constant with no equality-regression test guarding future drift.

## Next step

No `eval.md` exists yet for iter-30 (the formal goal-evaluator verdict was not available at summary time), so this is carried from the most recent evaluator guidance (iter-29's Next-Step Recommendation) plus this iteration's own phase spec. J-18 is done; continue the J-17..J-25 sequence, one new journey per iteration at FULL depth (each ships a new user-facing surface and/or a gate-adjacent change needing the audit/ux-regression/closure guards). The phase spec flags J-19 (dead-hypothesis graveyard, B-902 — reads this registry's lineage) as the natural next pick, with J-17 (statistical budget panel, B-903) as the other near-term candidate, followed by J-20/J-21 (daily-ops), J-22 (certifier audit), and J-23/J-24/J-25 (risk analytics). None of these carries an Evidence Claim, so none can collide with the current evidence-frontier plateau — never re-submit a closed FAIL.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-30-what-to-click.md`:

1. Open http://localhost:3255/research in your browser
2. Click the "Pre-registration registry" card
3. Wait for the table to finish loading
4. Look at the Status column for any row
5. Look at the Selectors column for any row

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-30.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-30-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-30-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-30-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-30-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-30-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-30-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-30-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-30-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-30-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-30-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-30-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-30-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
