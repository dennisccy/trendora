# Iteration Summary — goal-mcp-loop-iter-30

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-13
**Iteration:** 30

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open a fully auditable evidence ledger for every trading idea ever tested, and view up to thirty years of price history for any stock. Check a dashboard chart spanning three decades of major-index history alongside a volatility gauge and a rate-spread indicator, and use a Data Manager page showing a color-coded coverage calendar across the whole company list — the heaviest background data-refresh job now runs reliably without crashing anything. You can also now flip through the complete history of every trading idea the system has ever tried, in one browsable list, showing what was claimed, why, when it was written down, and what happened.

**What changed this time:** You can now open a full history of every trading idea the system has ever tried — including old ones — all in one place, with the reasoning behind each and how it turned out. Just as importantly, the system now automatically refuses to test any brand-new idea unless it was written down and registered ahead of time, closing a loophole where an idea could be quietly tried and only announced after it happened to work.

**What's next:** Next, the team plans to add a browsable list of ideas that didn't pan out, so nobody accidentally tries the same failed idea twice.

## Headline

Pre-registration registry ships: browsable hypothesis history + gate refuses unregistered claims

## Direction

**Signal:** improving
**Why:** iter-30 shipped J-18 (the pre-registration registry + fail-closed gate cross-check) cleanly through the full pipeline — Review PASS, QA PASS 30/30 backend + 15/15 functional, browser-QA 10/10, Audit PASS with zero fixes, Closure CLOSURE-PASS — flipping it from unknown to passing with no regressions across the nine required-still-passing journeys (J-01/02/03/05/06/07/08/09/11). Eight Must-have journeys (J-17, J-19..J-25) are still unbuilt, but the evaluator frames the remaining path as roughly eight more one-surface iterations, not a plateau.

**Trend (last 5 iters):**
- Newly passing this iter: J-18
- Newly passing in last 5 iters total: J-16 (iter-27), J-02, J-06, J-07, J-08, J-09 (iter-29), J-18 (iter-30)
- Regressions in last 5 iters: none (iter-26 was scored REGRESSION on a critical anti-goal violation — J-16 flipped unknown→failing there, not a passing→failing regression)
- Anti-goal violations in last 5 iters: 1 critical (anti-goal #8, full-universe backfill OOM crash, iter-26; resolved iter-27)
- Iters with no journey state change: 1 of last 5 (iter-28, a sanctioned plateau-assessment pass)

**Latest evaluator reasoning:** iter-30 shipped J-18, the governance keystone (pre-registration registry + fail-closed gate cross-check, backlog B-901), and it landed cleanly through the full pipeline. J-18 flips unknown -> passing; no journey regressed; no anti-goal was violated; coherence is COHERENCE-PASS. GOAL_ACHIEVED is not reachable — 8 Must-have journeys (J-17, J-19..J-25) remain unbuilt/unknown — so the loop continues.

## What was done

- Shipped the pre-registration registry page (`/research/registry`), listing all 11 historical trading-idea hypotheses with selectors, rationale, registration date, source, and status; discoverable from the Research hub in one click.
- Wired a machine-enforced gate: the certification pipeline now cross-checks every future Evidence Claim against the registry and refuses it — before any statistical test runs — if it wasn't pre-registered, closing the ad-hoc data-mining door for all future iterations.
- Backfilled the registry from both evidence ledgers (14 raw entries, 3 exact cross-ledger duplicates deduplicated to 11 hypotheses) plus the proposer-guidance candidate list; flipped the enforcement flag to on only after backfill completeness was test-proven.
- Added 30 new backend tests (loader, API endpoint, gate-enforcement fixtures) plus 3 config tests — all green; both evidence ledgers confirmed byte-identical before/after, canonical Bonferroni divisor unchanged at 8.
- Verified 1 target journey (J-18) passes browser QA — 10/10 test cases, 0 skipped — including graceful degradation on backend-down and missing-registry-file states.

## What's left

- Journey J-17 (the statistical budget is visible before it is spent) — unbuilt.
- Journey J-19 (dead hypotheses are browsable so nobody retries them blindly) — unbuilt; now unblocked since J-18's registry landed.
- Journey J-20 (a single daily preflight verdict guards every decision surface) — unbuilt.
- Journey J-21 (live data cannot silently diverge from the validated seed) — unbuilt.
- Journey J-22 (the certifier itself is calibrated) — unbuilt.
- Journey J-23 (the watchlist discloses its real concentration) — unbuilt.
- Journey J-24 (every stock shows an honest risk-budget card) — unbuilt.
- Journey J-25 (drawdown and dry-spell expectations are visible and honest) — unbuilt.

## Next step

iter-31 (FULL) — continue the J-17..J-25 backlog, one risky new surface per iteration (rubric rule 5). Best next target: **J-19 (dead-hypothesis graveyard, B-902)** — it reads the pre-registration registry's lineage links that J-18 just built and is now cleanly unblocked, so it consolidates the governance cluster the backlog wanted built first (B-903/B-901 before any wide scan; J-19 reads B-901). **J-17 (statistical-budget panel, B-903)** is the equally-ready alternative (the other governance surface). Each ships a new `/research/*` page + a served value, so FULL is warranted (new user-facing surface needing the audit/ux-regression/closure guards). Every J-17..J-25 journey carries NO Evidence Claim, so the canonical divisor stays 8 and no closed FAIL is ever re-submitted. Read the binding backlog card before planning each. Non-blocking carry-forwards (do NOT bundle): audit O1 — add a one-line `registry._CLAIM_SELECTOR_KEYS == tools._CLAIM_SELECTOR_KEYS` equality regression test (cheap drift insurance); audit O2 — tighten QA TC-12's keyword-scan wording (the page subtitle legitimately contains "certify" in governance-describing context). After ~8 more one-surface iterations J-17..J-25 close and GOAL_ACHIEVED becomes reachable — this is a clear tractable path, not a plateau.

## Assumptions made

- iter-30 · goal-evaluator — Ambiguity: The iter-30 DoD literally reads "Backfill complete: registry contains ... (≥14 ledger-derived rows)", but the committed registry has 11 rows; the goal text leaves open whether the literal "≥14" or the substantive dedup clause is the binding requirement. We chose: Scored the backfill-completeness line as MET by 11 rows, treating "≥14" as the decomposer's uncomputed estimate and the substantive dedup clause as the real bar — 14 raw ledger entries contain 3 exact cross-ledger duplicate selector-sets, forcing 11 as the mathematically correct count, confirmed by round-trip tests and independently re-derived by the reviewer and auditor. Reversible: yes
- iter-30 · goal-decomposer — Ambiguity: B-901's backfill instruction leaves the scope of "every registered hypothesis" open — canonical ledger only, or the union of both ledgers plus the pre-registered candidate tables. We chose: Backfill = the union of the pre-registered candidate rows and every distinct claim selector-set across both ledgers, deduplicated by hypothesis, each labeled with source + status (including the closed ma_stack FAIL as a closed row) — the honest superset the enforcement gate and the next journey's graveyard need. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-02's acceptance requires the three inline "Not yet proven" score badges to be visible on the stock detail page, but the captured frames show the badges below the fold, with no direct pixel of them. We chose: Scored J-02 passing on the visible negative assertion (no fabricated proof panel) plus multi-channel corroboration (DOM assertions, factor-lab page, leaderboard instances, zero code diff) in lieu of a direct pixel, mirroring an earlier iteration's precedent. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: browser QA marked five evidence journeys "PASS (see note)" on their honest-status half, but each journey's written acceptance requires a Proven edge to surface or drill into, which doesn't exist on the all-FAIL ledger. We chose: Held all five at partial, not passing, per strict journey acceptance and a multi-iteration sanctioned-partial precedent — an honest all-FAIL rendering satisfies the anti-fabrication guardrail but not the journey's own acceptance text. Reversible: yes
- iter-28 · goal-decomposer — Ambiguity: the goal's loop mechanics leave open how many iterations to keep re-attempting the five evidence journeys when a staging exploration surfaces no promotable edge — keep trying vs. acknowledge a plateau. We chose: A verify-only / plateau-acknowledgement pass with no new Evidence Claim, after confirming on disk that the complete pre-registered candidate set is already exhausted and all-FAIL; surfaced the remaining unblock (a human revision of the registry) to the evaluator rather than manufacturing a claim. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether the no-hard-coded-credentials anti-goal covers the vendored framework's own judgment-eval test fixtures (12 planted fake keys) or only the product's own source. We chose: Read the anti-goal as scoped to the product source; the product diff carries zero credentials and the flagged keys are non-real fixtures whose purpose is to be flagged — scored upheld, not a violation. Reversible: yes
- iter-26b · goal-evaluator — Ambiguity: the target journey's proof crashed the backend but its perf/byte-identity half was real and one honest-progress sub-criterion showed positive, so the journey could arguably be read as partial rather than failing. We chose: Scored failing, because there is a verified negative outcome (a reproduced backend-wide crash) and the journey's own definition of done explicitly requires no-crash — this session reserves partial for "correct-but-not-cleanly-verified," not a verified failure. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: whether this iteration caused the critical anti-goal violation (a memory crash) or merely surfaced a pre-existing latent issue while probing a heavier job path. We chose: Scored REGRESSION because a critical anti-goal is demonstrably, reproducibly violated and unresolved — the verdict does not depend on this-iteration causation, matching the auditor's and ux-regression reviewer's reasoning and the framework's fail-closed rule for critical anti-goal violations. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-30-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
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
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-30/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
