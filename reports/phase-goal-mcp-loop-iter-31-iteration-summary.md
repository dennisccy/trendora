# Iteration Summary — goal-mcp-loop-iter-31

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-13
**Iteration:** 31

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open a fully auditable evidence ledger for every trading idea ever tested (including a browsable registry of every idea that was written down and registered before it was tested), and view up to thirty years of price history for any stock. See a dashboard chart spanning three decades of major-index history alongside a volatility gauge and a rate-spread indicator, and use a Data Manager page with a color-coded coverage calendar — the heaviest background data-refresh job now runs reliably without crashing. You can now also browse a "graveyard" of every idea the system has tested and rejected, see exactly why each one failed, and read the rule for when (if ever) a rejected idea could be tried again.

**What changed this time:** You can now browse a graveyard of every idea the system has tested and rejected — including, for the first time, ideas from its internal early-research track, not just the one shown publicly before. Each entry shows exactly why it was rejected, the one idea that's permanently retired is clearly flagged, and every entry links to a plain-language rule for when (if ever) a rejected idea could be tried again. One small rough edge was found and fixed along the way: a link meant to jump straight to an idea's original registration didn't always scroll to the right spot — that's been corrected, though it's still waiting on one final double-check.

**What's next:** Next, the team plans to add a page that shows how much statistical testing "budget" is left before new ideas can be tested, along with a handful of daily health-check and risk-related views.

## Headline

Negative-results graveyard ships: browse every rejected hypothesis + its revisit rule (J-19)

## Direction

**Signal:** holding
**Why:** iter-31 shipped and substantially verified J-19 (the negative-results graveyard) — closure passed clean, no regression occurred, and the one P1 browser-QA failure (UT-07, a lineage link that didn't auto-scroll to its target row) was root-caused, fixed, and independently re-verified live by the audit. No `eval.md` exists yet for this iteration (the goal-evaluator has not scored it), and the canonical browser-QA artifact itself still reads FAIL on that case, so — consistent with this session's iter-13/20/22 precedent that an audit-applied fix is not a substitute for a clean canonical re-run — journey-history is not yet updated and the signal stays conservative pending that confirmation.

**Trend (last 5 iters):**
- Newly passing this iter: not yet scored — `eval.md` for iter-31 does not exist; browser-QA + audit evidence suggest J-19 is close, but the canonical lane's own artifact still reads FAIL on UT-07 pending a clean re-run
- Newly passing in last 5 iters total (iters 27-31): J-16 (iter-27), J-02/J-06/J-07/J-08/J-09 (iter-29), J-18 (iter-30)
- Regressions in last 5 iters: none (iters 27-31)
- Anti-goal violations in last 5 iters: none new in iters 27-31 (the two critical anti-goal #8 violations occurred in iter-24 and iter-26, both already resolved and outside this window)
- Iters with no journey state change: 1 of last 5 (iter-28, a sanctioned plateau-assessment pass); iter-31 not yet scored

**Latest evaluator reasoning:** iter-30 delivered J-18 cleanly through the full pipeline, and I verified every load-bearing claim against artifacts I personally opened, not the handoffs. NOT GOAL_ACHIEVED (J-17/J-19..J-25 unknown — no Must-have may be unknown at achievement). NOT REGRESSION (no passing->failing; no critical anti-goal; engine + ledgers byte-identical). NOT STALLED (progress made — J-18 flipped; 8 tractable unbuilt journeys remain with binding backlog cards). NOT ESCALATE (already full; review PASS not fail-open; no journey failed two consecutive iters — J-18 passed first try). CONTINUE, full.

## What was done

- Shipped `/research/graveyard`, a new read-only page listing all 14 hypotheses the referee has rejected (7 from the canonical evidence ledger + 7 from the internal staging ledger) with selectors, verdict, date, deflation context, ledger origin, and registration lineage.
- Flagged the one permanently-closed hypothesis (`ma_stack`) with a "permanent" marker and added a "Revisit protocol" panel explaining exactly when a rejected idea may ever be re-tested; every row links to it.
- Added the backend composition module `app.engine.graveyard` + `GET /api/research/graveyard`, reusing the existing registry lineage-matcher (no reimplementation) and a second "Governance & process" card on the Research hub.
- Added 45 new/extended backend tests (18 graveyard + 4 API + 1 drift-insurance in the registry suite) — all green; `tsc --noEmit` clean; all three ledger/registry state files confirmed byte-identical before and after (no regression mechanism).
- Browser QA ran live: 11 of 14 cases passed; the one P1 failure (a lineage link that didn't auto-scroll to its target row on in-app navigation) was root-caused, fixed, and independently re-verified live by the audit (scroll position moved from 0 to 584, landing the row just below the header).

## What's left

- The canonical browser-QA artifact for J-19 still records a FAIL on UT-07 (lineage-link scroll); the fix is applied and the audit independently re-verified it live, but no clean canonical browser-qa re-run has been recorded yet, and the goal-evaluator has not yet scored this iteration.
- Two J-19 browser sub-tests (empty-ledger state, loading skeleton) were skipped for tooling/permission reasons; both are covered by passing backend fixture tests but not yet observed live in a browser.
- Journeys J-17 (statistical budget visible before it's spent), J-20 (daily preflight readiness verdict), J-21 (live-data drift guard), J-22 (referee self-check), J-23 (watchlist concentration view), J-24 (per-stock risk-budget card), and J-25 (drawdown/dry-spell expectations panel) all remain unbuilt.
- The frontend's pure-logic test harness (`node lib/*.test.ts`) still cannot run in this sandbox — a pre-existing environment gap, not something this iteration caused.

## Next step

No `eval.md` exists yet for this iteration — the goal-evaluator has not scored iter-31. Per the audit's own recommended next step: proceed to the next iteration — J-19's definition-of-done is met and the one browser-QA FAIL (UT-07, lineage-link scroll) is resolved and independently browser-verified in the audit; optional non-blocking follow-ups are a browser-QA re-run to record a clean passing UT-07 evidence frame, and live execution of the two skipped states (empty-ledger, loading-skeleton). Per the iter-30 evaluator's own roadmap (with J-19 now shipped), the next FULL target is most likely **J-17** (statistical-budget panel, B-903) or **J-20** (daily preflight/readiness verdict) — read the relevant backlog card before planning. Each remaining journey (J-17, J-20–J-25) carries no Evidence Claim, so the canonical Bonferroni divisor stays at 8 and no closed FAIL should ever be re-submitted.

## Assumptions made

- iter-31 · goal-decomposer — Ambiguity: J-19's "every non-PASS verdict" plus B-902's "read-compose from ledgers" left open whether the staging ledger's non-PASS verdicts are in scope (the blueprint had declared staging "internal-only, never served") and whether the composition happens backend- or frontend-side. We chose: surface both ledgers' non-PASS verdicts via a new backend composition endpoint (`GET /api/research/graveyard`), preserving the honesty fence (no proven-language from staging; `/evidence`/`proven_signals`/the "Proven" badge stay byte-identical). Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: The iter-30 DoD literally reads "Backfill complete: registry contains ... (≥14 ledger-derived rows)", but the committed registry has 11 rows; the goal text leaves open whether the literal "≥14" or the substantive dedup clause is the binding requirement. We chose: Scored the backfill-completeness line as MET by 11 rows, treating "≥14" as the decomposer's uncomputed estimate and the substantive dedup clause as the real bar. Reversible: yes
- iter-30 · goal-decomposer — Ambiguity: B-901's backfill instruction leaves the scope of "every registered hypothesis" open — canonical ledger only, or the union of both ledgers plus the pre-registered candidate tables. We chose: Backfill = the union of the pre-registered candidate rows and every distinct claim selector-set across both ledgers, deduplicated by hypothesis. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-02's acceptance requires the three inline "Not yet proven" score badges to be visible on the stock detail page, but the captured frames show the badges below the fold, with no direct pixel of them. We chose: Scored J-02 passing on the visible negative assertion plus multi-channel corroboration in lieu of a direct pixel. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: browser QA marked five evidence journeys "PASS (see note)" on their honest-status half, but each journey's written acceptance requires a Proven edge to surface or drill into, which doesn't exist on the all-FAIL ledger. We chose: Held all five at partial, not passing, per strict journey acceptance. Reversible: yes
- iter-28 · goal-decomposer — Ambiguity: the goal's loop mechanics leave open how many iterations to keep re-attempting the five evidence journeys when a staging exploration surfaces no promotable edge. We chose: A verify-only / plateau-acknowledgement pass with no new Evidence Claim, surfacing the remaining unblock to the evaluator rather than manufacturing a claim. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether the no-hard-coded-credentials anti-goal covers the vendored framework's own judgment-eval test fixtures (12 planted fake keys) or only the product's own source. We chose: Read the anti-goal as scoped to the product source; scored upheld, not a violation. Reversible: yes
- iter-26b · goal-evaluator — Ambiguity: the target journey's proof crashed the backend but its perf/byte-identity half was real, so the journey could arguably be read as partial rather than failing. We chose: Scored failing, because there is a verified negative outcome and the journey's own definition of done explicitly requires no-crash. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: whether this iteration caused the critical anti-goal violation (a memory crash) or merely surfaced a pre-existing latent issue. We chose: Scored REGRESSION because a critical anti-goal is demonstrably, reproducibly violated and unresolved — the verdict does not depend on this-iteration causation. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-31-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
2. Click the "Negative-results graveyard" card
3. Wait for the table to finish loading
4. Find the row whose Selectors chips include `factor=ma_stack`
5. Click that row's Lineage link (reads `factor-ma_stack-d10-h20 →`)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-31.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-31-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-31-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-31-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-31-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-31-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-31-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-31-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-31-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-mcp-loop-iter-31-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-31-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-31-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-31-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
