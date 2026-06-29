# Iteration Summary — goal-mcp-loop-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-29
**Iteration:** 1

## In plain words

**What you can do now:** See a "Not yet proven" evidence status chip next to every Leadership, Entry Quality, and Risk score on the stocks leaderboard and on individual stock pages. Open a dedicated Evidence page from the left navigation in one click to see the certified-claims ledger (currently empty, with an honest explanation of what each future certified claim will show).

**What changed this time:** Every stock score now shows a small "Not yet proven" label beside it — so each score and its evidence status appear together for the first time. A new Evidence page appeared in the left sidebar, giving you a place to audit all certified statistical claims. Today it honestly says "No certified claims yet" and shows the five fields each future certified claim will carry.

**What's next:** Next we'll certify the first statistical claim through the referee review process, wire it to a drill-down panel, and stamp the ledger entry with the signal it backs — so a badge can flip to "Proven" and let you click through to the out-of-sample test results behind it.

## Headline

Evidence status chips on every stock score; new Evidence ledger page live with honest empty state

## Direction

**Signal:** improving
**Why:** J-01 (Every score shows an evidence status) and J-03 (Unproven / noise signals are honestly marked) are newly passing this iteration, verified by browser QA with real screenshots across 120 leaderboard rows and the MU stock-detail page. J-05 advanced to partial — the Evidence page and nav entry are live and confirmed, with the populated-claim audit steps gated on the first certified claim. No regressions occurred and the next step (certifying the first claim in iter-2) is clearly scoped.

**Trend (last 2 iters):**
- Newly passing this iter: J-01, J-03
- Newly passing in last 2 iters total: J-01, J-03
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 1 of last 2 (iter-0)

**Latest evaluator reasoning:** The full pipeline ran cleanly and captured real browser evidence (closing the iter-0 gap): the read-side evidence path is live end to end. Against the absent/empty ledger, every score on `/stocks` and stock-detail honestly renders "Not yet proven" and the nav-reachable `/evidence` page shows an honest empty state — so J-01 and J-03 are newly verified passing and J-05's ledger surface is delivered. Nothing is presented as "Proven" (no certified claim exists), no anti-goal was violated, and coherence passed — but J-02, J-04, and J-05's populated-claim audit (steps 2-3) all need the first referee-certified claim, so the goal is not yet achieved.

## What was done

- Built read-side evidence resolver (`app.engine.evidence`): reads certified-claims ledger via `app.engine.ledger.read_entries`; a signal is Proven only on a `verdict.status == PASS` entry with a named signal key; absent/empty ledger → `{claims: [], proven_signals: {}}` (fail-safe)
- Added typed config `evidence.ledger_path` to `config.py` + `config.yaml` (default `runs/goal-session-mcp-loop/state/certified-claims.jsonl`; `TRENDORA_LEDGER_PATH` env override supported); no path literal in application code
- New read-only endpoint `GET /api/evidence` registered in `main.py`; absent ledger → 200 empty, never 500; recomputes nothing
- New `EvidenceStatusBadge` component rendering "Not yet proven" (muted) or "Proven" (linking to `/evidence#signal-<key>`); fail-safe default is "Not yet proven"
- Inline evidence badges on every `/stocks` leaderboard row (one per score column, non-blocking fetch) and each `/stocks/[ticker]` ScoreCard; served scores confirmed byte-identical via regression test
- New `/evidence` ledger page with honest empty state, five-field claim-row layout, and claim→surface linkback; new Evidence nav entry (ShieldCheck icon, inserted after Research); 25/25 Next.js routes compiled clean
- Verified J-01, J-03, and J-05 surface via full-pipeline browser QA: 13/15 PASS (2 P2/P3 skipped — DevTools network-blocking not automatable via Chrome MCP), 4 screenshots captured in `reports/qa/goal-mcp-loop-iter-1-evidence/`

## What's left

- Journey J-02 (Drill into the proof behind a score) — deferred/unknown; needs at least one referee-certified PASS claim and a drill panel showing the OOS test result, control comparison, and certified-claim id + registration date
- Journey J-04 (Regime-conditioned evidence) — deferred/unknown; needs regime-scoped certified evidence labeled with the regime it holds in
- Journey J-05 (Audit the evidence ledger) — partial; populated claim row and click-through claim→surface linkback are built and unit-tested but not exercisable until the first certified claim is registered
- Ledger writer (`app.mcp.tools.verify_edge`) does not yet stamp `claim.signal` — even a genuine referee PASS entry stays "Not yet proven" on all badges until that wiring is added (prerequisite for J-01's/J-02's "Proven" path to appear)
- Evidence status badges on `/sectors`, `/themes`, and Research lab pages — deferred to a later iteration

## Next step

Run iter-2 as the **first certified iteration** (full depth): propose a narrow, regime-conditioned machine-readable `## Evidence Claim` JSON block that earns a referee **PASS** at the post-decompose gate (prefer a tight, regime-scoped cohort — the referee counts independent holdout *dates*, not correlated same-date names, and deflates for every claim ever tested). Two things must land together for the PASS to actually light up a badge:

1. **Wire the ledger writer to stamp `claim.signal`.** Per the dev handoff's known issue, the real `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with **no `signal` key**, and the read side keys `proven_signals` on `claim.get("signal")` (fail-safe) — so even a genuine referee PASS would stay "Not yet proven" until the writer stamps the canonical signal key (`leadership_score` / `entry_quality_score` / `risk_score`). Closing this is the prerequisite for J-01's/J-02's "Proven" path to ever appear.
2. **Build the J-02 drill panel** on stock-detail: a "Proven" badge expanding to the out-of-sample test result, the control comparison (vs SPY/QQQ/sector/random), and the certified-claim id + registration date — read verbatim from `/api/evidence`.

That single certified iteration advances **J-02** (drill panel), completes **J-05** end-to-end (a populated claim row + claim→surface linkback, steps 2-3), and lays the groundwork for **J-04** (label the claim with the regime it holds in). Full depth is warranted because it ships a new "Proven" data surface gated by the referee and adds new drill UI needing the browser-QA / ux-regression / closure lanes. Optionally fold in the coherence WARN cleanup (extract `SCORE_SIGNALS` to `apps/frontend/lib/evidence.ts`) — advisory, not required.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-1-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-1-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-1-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-1/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
