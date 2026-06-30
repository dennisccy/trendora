# Iteration Summary — goal-mcp-loop-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-30
**Iteration:** 2

## In plain words

**What you can do now:** Browse the stock rankings and see an evidence status — "Proven" or "Not yet proven" — beside each Leadership, Entry Quality, and Risk score on every row. The Leadership score is now the platform's first signal to earn a green "Proven" badge, the result of a rigorous sealed statistical review. Visit the dedicated Evidence page from the sidebar to read the certified claim record. On any stock's detail page, a "Why proven?" button below the Leadership score expands to show the exact numbers behind the certification: out-of-sample test result, comparison against SPY, and the date it was certified. (The proof-drill feature is code-complete and unit-tested; a final browser check is still pending.)

**What changed this time:** Behind the scenes, the first statistical certification was completed — the Leadership score survived a sealed out-of-sample test (p ≈ 0.0005, +6.36% edge vs SPY, 12,297 observations) and is now permanently recorded as "Proven" in the ledger. The code to display those proof details in a browser was also built and unit-tested. However, a setup issue prevented the automated browser check from running this round — the test browser could not reach the backend — so the visual confirmation is still outstanding.

**What's next:** Next we'll fix the test-environment connection issue so the browser can reach the backend, then run a full browser check confirming the "Proven" badge, the "Why proven?" proof panel, and the Evidence ledger round-trip all work as shipped.

## Headline

First 'Proven' score end to end — Leadership score backed by statistically certified claim; browser verification pending

## Direction

**Signal:** holding
**Why:** Iter-2 landed the session's first referee-certified claim in the ledger and `/api/evidence` now serves `proven_signals.leadership_score.proven==true`, but all 18 browser tests were SKIPPED due to a harness frontend→backend connectivity failure (frontend stuck on "Checking backend…", empty leaderboard). J-02 (proof drill-down) stays unknown and J-05 (evidence ledger) stays partial — both data-layer-unblocked but UI-unverified. J-01 and J-03 carry as passing from iter-1 with no regression evidence; no anti-goal violations. Direction is holding: a real backend milestone was reached but no journey state changed.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-01, J-03
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 2 of last 3 (iter-0 and iter-2)

**Latest evaluator reasoning:** The backend half of this iteration genuinely succeeded: the post-decompose gate's referee certified the first claim (top decile of `leadership_score`, sealed holdout 279 dates, SPY control n=1137, bonferroni, p=0.0004998 < 0.05 → PASS), the ledger entry carries the canonical `signal`, and `GET /api/evidence` now serves `proven_signals.leadership_score.proven == true` (curl-verified, byte-identical to the ledger). The proof-panel code shipped, is unit-tested, builds clean, and is coherence- and review-clean with no anti-goal violations. However, the browser-QA lane verified nothing — `status.json` has `browser_checks_run: false`, all browser tests SKIPPED (frontend stuck on "Checking backend…", empty leaderboard), no audit handoff was produced, and the lone screenshot shows a broken/empty page rather than any passing journey. The user-facing target journeys J-02 and J-05 are therefore unproven despite the data being in place.

## What was done

- Post-decompose referee certified the first claim: top decile of `leadership_score`, horizon 20, vs SPY, sealed holdout 279 dates, p=0.0004998 < 0.05, n=12,297 — first entry appended to `certified-claims.jsonl`
- `/api/evidence` now serves `proven_signals.leadership_score.proven==true` (backend read path unchanged; zero new computation)
- Built `ScoreProofPanel` client component — "Why proven?" disclosure on `/stocks/{ticker}` revealing OOS test result, SPY control comparison, and certified-claim id + date; renders nothing for unproven signals (fail-safe)
- Wired `ScoreProofPanel` to Leadership score card on stock-detail; Entry Quality + Risk cards visually unchanged
- Added backend `_resolve_signal()` hardening in `app.engine.evidence` — derives UI signal for score-column PASS entries missing an explicit `signal` field (display-routing only; defense-in-depth for future claims)
- Extracted shared `SCORE_SIGNALS` + proof helpers (`proofFieldsFor`, `formatEvidencePct`, `formatPValue`) into `apps/frontend/lib/evidence.ts`, removing duplicate definitions from both stocks pages (clears coherence WARN)
- All tests passed: 9/9 backend evidence unit tests, 3/3 API endpoint tests, 10/10 frontend unit tests; production build clean (`tsc --noEmit` + `next build`, exit 0)
- Browser-QA lane: 0/18 tests executed — frontend-to-backend connectivity failure in harness; lone screenshot shows empty leaderboard with "Checking backend…"

## What's left

- Journey J-02 ("Drill into the proof behind a score") — unknown; `ScoreProofPanel` shipped + gate PASS + API `proven==true`, but no browser verification; must be browser-confirmed in iter-3
- Journey J-05 ("Audit the evidence ledger") — partial; populated claim row exists at the data layer but populated-row render + "Backs: Stocks leaderboard →" linkback round-trip not browser-verified
- Journey J-01 ("Every score shows an evidence status") — carried passing from iter-1; needs re-confirmation after harness fix (Leadership badge has changed from "Not yet proven" to "Proven")
- Journey J-03 ("Unproven / noise signals are honestly marked") — carried passing from iter-1; needs re-confirmation that only Leadership reads "Proven" and Entry Quality + Risk remain "Not yet proven"
- Journey J-04 ("Regime-conditioned evidence") — unknown; correctly out of scope iter-2; requires a regime-conditioned certified claim in a future iteration
- Fix test-harness root cause: frontend :3255 cannot reach backend :8255 — service-start ordering, API base URL, or health-proxy issue

## Next step

Run iter-3 as a **full browser-verification pass of already-shipped code — do NOT rebuild the dev work** (it is reviewed, unit-tested, coherence-clean, and the certified claim is already in the ledger). Priorities: (1) Fix the test-harness root cause first — the frontend at :3255 cannot reach the backend at :8255 ("Checking backend…" stuck, empty leaderboard / no regime / no themes). (2) Browser-verify J-02 end-to-end: `/stocks` → click a stock → expand "Why proven?" → assert the OOS test (status/holdout edge/p-value/cohort n), the "vs SPY (benchmark control)" excess, and the claim id + `registered 2026-06-30`, byte-identical to `/api/evidence`. (3) Browser-verify J-05 end-to-end: `/evidence` populated `leadership_score` row (5 fields) + "Backs: Stocks leaderboard →" linkback round-trip, and leaderboard "Proven" badge → `/evidence#signal-leadership_score`. (4) Re-confirm badge flip + regressions (J-01, J-03): real screenshot of Leadership badge reading "Proven" on `/stocks` AND stock detail, with Entry Quality + Risk still "Not yet proven." Treat `browser_checks_run: false` + an all-SKIP ui-test-results as a hard verification gap — a QA PASS must not be granted on build+units+API alone.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-2-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-2-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-2-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-2/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
