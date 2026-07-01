# Goal Session mcp-loop — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-29T20:53:00Z

**Verdict:** ESCALATE
**Lesson:** The lean pipeline silently produced NO browser-QA evidence this iteration — telemetry.jsonl had no `browser-qa-agent` record (the sequence jumped reviewer → goal-evaluator), status.json stayed at `current_step: dev_complete` / `browser_checks_run: false`, and neither `reports/phase-<iter>-ui-test-results.md` nor the expected SKIPPED stub (goal-iter-lean.sh:392) was written. Do not infer journey pass/fail from the developer's static code scan; confirm the browser-qa-agent actually ran before scoring, and seed journeys as `unknown` (not `failing`) when it did not.
**Applies to:** any lean iteration / any baseline iter-0 — the evaluator should verify a `browser-qa-agent` telemetry record + a non-empty evidence dir BEFORE recording journey verdicts; a missing ui-test-results file should drive ESCALATE (force full), per goal-iter-lean.sh's own design intent (lines 185, 396).

## iter-1 — 2026-06-29T22:37:16Z

**Verdict:** CONTINUE
**Lesson:** The read-side "Proven" path is built but cannot light up yet: the real ledger writer `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with NO `signal` key, while the read side keys `proven_signals` on `claim.get("signal")` (fail-safe). So even a genuine referee PASS would map to NO UI signal and stay "Not yet proven" — the first certified iteration MUST stamp the canonical signal key (`leadership_score`/`entry_quality_score`/`risk_score`) on the written claim, or J-01/J-02's Proven badge will silently never appear despite a passing ledger entry. (Also: against an empty ledger, J-05 steps 2-3 — populated claim row + claim->surface linkback — are structurally un-exercisable, so J-05 caps at `partial` until ≥1 claim is certified; don't score it `passing` on the empty-state surface alone.)
**Applies to:** the first certified iteration and any iter proposing a `## Evidence Claim` / touching `app.mcp.tools.verify_edge`, `app.engine.evidence`, or the `/evidence` page — verify the writer stamps `claim.signal` and that a PASS actually flips a badge end-to-end (browser-verified), not just that the ledger row exists.

## iter-2 — 2026-06-30T01:08:00Z

**Verdict:** CONTINUE
**Lesson:** A FULL iteration's QA agent returned PASS / "READY TO SHIP" while SKIPPING every browser test (frontend stuck on "Checking backend..." → empty leaderboard at /stocks), justifying it with build+units+API-curl alone; status.json honestly recorded browser_checks_run=false and no audit handoff was produced. This is exactly the over-trust the iter-1 lesson warned against: a certified ledger row + green build/units/API is NOT proof the user-facing badge flip and proof-drill render. The root cause was harness connectivity (frontend :3255 could not reach backend :8255), not application code — but it silently nullified the iteration's entire verification value.
**Applies to:** any goal-mode iteration whose Definition of Done is user-journey/browser-verification — treat browser_checks_run=false OR an all-SKIP ui-test-results.md as a HARD verification gap (journeys stay unknown/partial, never passing), regardless of a QA PASS. Before re-running the browser lane, confirm the frontend can actually reach the backend (service-start order, API base URL, health proxy) — a single empty-leaderboard screenshot is the tell.

## iter-3 — 2026-06-30T02:42:00Z

**Verdict:** CONTINUE
**Lesson:** Browser-QA captured four screenshots named for the expanded "Why proven?" proof panel (UT-07/UT-08/TC-05/UT-16) that were byte-identical full-page-top frames — the panel renders BELOW the fold and was never actually in any captured viewport. J-02 was only confirmable because the identical OOS values (PASS/+6.36%/p=0.0004998/n=12,297/vs SPY/registered 2026-06-30) render in a clear frame on /evidence (UT-12, single source of truth) AND the in-panel linkback navigated (UT-09). A screenshot named for a disclosure/expander proves nothing about the expanded state unless the target element was scrolled into the viewport first.
**Applies to:** any iter that browser-verifies an expand/disclose/drill-down/below-the-fold interaction — next up J-04's regime-conditioned evidence panel. The browser-qa-agent must scroll the target element into frame before capturing, and the evaluator should treat a panel-named screenshot that only frames the page header as a visual-evidence gap (lean on an independent same-value render + a confirmed in-component link as corroboration, never the named screenshot alone).

## iter-4 — 2026-06-30T04:05:00Z

**Verdict:** CONTINUE
**Lesson:** There are TWO independent browser lanes and they can DISAGREE: the canonical
`browser-qa-agent` (writes `reports/phase-<iter>-ui-test-results.md`, UT-* screenshots) and the QA
agent's own Chrome MCP run (writes `reports/qa/<iter>-qa.md`, TC-* screenshots). In iter-4 the canonical
lane reported all 11 SKIP ("frontend not running") while the QA lane PASSED 15/15 with real working
screenshots — root cause: a stale `next-server` held :3255 serving an old bundle, and `start-frontend.sh`
(unlike `dev.sh`) does NOT `fuser -k` the port before binding, so whichever lane ran first hit EADDRINUSE
/ stale UI. The fix is operational: free :3255 before the browser-qa lane binds. Evaluator discipline: a
parallel QA-lane PASS (even with genuine pixels) does NOT substitute for the canonical lane on the
terminal GOAL_ACHIEVED gate — withhold success until the canonical lane renders all journeys and the
post-QA audit handoff exists (the audit stage stopped at `qa_complete` in both iter-3 and iter-4).
**Applies to:** any browser-verified iteration, especially the terminal GOAL_ACHIEVED gate — check both
`ui-test-results.md` (canonical) AND `<iter>-qa.md` (QA lane); reconcile a SKIP-vs-PASS split via the
port; and confirm `start-frontend.sh` frees the frontend port before binding.

## iter-5 — 2026-06-30T05:30:00Z

**Verdict:** CONTINUE
**Lesson:** The iter-4 diagnosis ("canonical lane SKIPs because a stale next-server holds the frontend port") was only ONE of the failure modes, and not the one that bit iter-5. The iter-5 port-free fix to `scripts/start-frontend.sh` is correct but the canonical browser-qa-agent lane never reached the port-binding step: per `runs/goal-session-mcp-loop/engine.log` L402-413 the post-dev parallel **Branch-UI** chain aborted upstream at `ui-test-design` ("phase-*-user-visible-changes.md not found" even though `ui-impact-phase.sh` reported writing it), so browser-qa-agent + ux-regression + closure never ran AND `reports/phase-*-iter-5-ui-test-results.md` was wholly absent (not all-SKIP). Separately, the `update_status` call with `invalid step 'post_dev_parallel_complete'` (L412-413, also iter-4 L343) makes the "sequential retry" fallback bail, which is why the AUDITOR has now failed to run three iterations running (iter-3/4/5). Net: when a verification artifact is missing, read `engine.log` to find WHERE the pipeline actually died — don't assume the previously-hypothesised cause; and never let QA-parallel-lane (`reports/qa/*-qa.md`) UT-*-named screenshots stand in for the canonical lane (`reports/phase-*-ui-test-results.md`), especially when they contain byte-identical duplicates (UT-07≡UT-09 here).
**Applies to:** any goal-mode iteration whose DoD depends on the canonical browser-qa-agent lane or the post-QA auditor running — i.e. any iter that must flip a journey partial→passing via fresh canonical pixels, or that lists the audit handoff as a DoD item. Check `engine.log` for `Branch-UI ... aborting chain` and `invalid step 'post_dev_parallel_complete'` before trusting any GOAL_ACHIEVED.

## iter-6 — 2026-06-30T06:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A harness defect that must take effect *mid-run* has to live in a component re-invoked as a fresh subprocess each step — here the child scripts (`ui-impact-phase.sh`/`ui-test-design-phase.sh` rc==0 post-condition guards) and `lib/verdicts.py` (the `post_dev_parallel_complete` enum) fixed the canonical-lane + auditor aborts the same run, whereas the `run-phase.sh:645-651` parent edit only lands on the next dispatch (bash tracks a running parent by byte offset). Three straight iters stalled because the real death points (engine.log: ui-impact phantom "Done" → ui-test-design missing-file abort at 04:40:01, and the invalid-step abort at 04:43:47) sat two steps upstream of the port fix iter-5 chased. Separately, `browser_checks_run` in status.json is a DEAD flag — no harness path ever sets it true — so never gate GOAL_ACHIEVED on it; judge on the canonical `…-ui-test-results.md` + engine.log.
**Applies to:** any goal-mode iteration that repairs the verification harness mid-run, and any future goal-evaluator run that sees `browser_checks_run:false` despite a real canonical-lane PASS.

## iter-8 — 2026-06-30T22:12:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A GENERAL read-side cohort matcher (`resolveCohortEvidence` in `apps/frontend/lib/evidence.ts`) lights "Proven" on EVERY certified cohort it matches — including a score-column factor (`leadership_score`) that also appears as a factor-lab row. The spec's parenthetical only named vcp_contraction, but lighting leadership_score too is HONEST and correct (it has a genuine PASS ledger entry; anti-goal #1 only bans UNBACKED "Proven"), NOT a defect — provided the badge deep-links via `claimAnchorId` to the row's REAL `signal-…` anchor and not a `factor-…` cohort anchor the row never carries. Do not "fix" this by special-casing the matcher to vcp-only; suppressing a true status would be the dishonest move.
**Applies to:** any iter that touches the factor-lab evidence matcher / `resolveCohortEvidence` / `claimAnchorId`, or adds a new certified cohort whose factor doubles as a score-column row — expect (and allow) every certified cohort to read "Proven", and assert the deep-link lands on the row's actual anchor.

## iter-9 — 2026-07-01T01:52:58Z

**Verdict:** CONTINUE
**Lesson:** For a backend-only refactor of a *shared value's computing module* (here referee/ledger/verify_edge behind every "Proven" badge), the regression proof is NOT a browser pass — it is (a) the shared value's canonical output being git-UNMODIFIED / byte-identical (`certified-claims.jsonl` + `GET /api/evidence` frozen-golden) and (b) the module's existing default-path tests being UNEDITED and green (`git diff test_referee.py` == 0 lines). An unedited passing suite is the strongest possible proof "defaults reproduce today"; if a future iter had to EDIT those expectation tests, that is itself the regression signal. Judge on this, never on the dead `browser_checks_run` flag or a SKIPPED browser lane (which is correct for a no-frontend-diff iter).
**Applies to:** any iter touching `apps/backend/app/engine/{referee,ledger,forward_walk}.py` or `app/mcp/tools.py:verify_edge` (the shared certification engine) — especially the upcoming iter-10/iter-11 that reuse this economy.

## iter-9b — 2026-07-01T01:52:58Z

**Verdict:** CONTINUE
**Lesson:** iter-9 flipped the gate's default ledger to `"staging"` (`project-extensions/gates/verify_claim.py`) — the conservative direction (a forgotten key ⇒ "not shown as proven", never "wrongly proven"). But this is a real footgun for the very next iterations: a J-07/J-08 winner meant for the user-facing badge that omits `"ledger":"canonical"` in its `## Evidence Claim` gets certified into the internal staging ledger and SILENTLY never surfaces on `/evidence` or the factor lab — the journey would fail to build with no gate error. The badge-bound claim MUST set `"ledger":"canonical"` explicitly.
**Applies to:** iter-10 (J-07 multi-horizon) and iter-11 (J-08 combination) — any iter whose Evidence Claim is intended to light a user-facing "Proven" badge.

## iter-10 — 2026-07-01T04:19:25Z

**Verdict:** CONTINUE
**Lesson:** When a staging discovery clears the bar at the block-bootstrap p-FLOOR (`p = 1/(B+1) = 0.00049975`), the p-value alone cannot rank winners — it is saturated. iter-10 found THREE h60 PASSes all at the identical p-floor, so the `holdout_edge` magnitude is the tiebreaker: `rs_spy_3m` h60's `+0.2134` edge is implausibly large (auditor B3 flagged it) next to `vcp_contraction` h60's modest `+0.089`. For canonical promotion prefer the signal-less winner with the more credible, modest edge — a p-floor PASS with an outsized edge is a yellow flag, not the strongest candidate. Two mechanical traps on promotion: (1) the gate defaults an omitted `"ledger"` key to `staging`, so a promotion `## Evidence Claim` MUST set `"ledger":"canonical"` EXPLICITLY or the winner is silently re-certified into staging and never surfaces; (2) a canonical PASS permanently appends to `certified-claims.jsonl` and tightens the user-facing Bonferroni divisor (5→6) forever — so promote only a candidate whose recorded raw p already clears required_p=0.010 (the iter-8 ma_stack bar-tightening disaster is the counter-example).
**Applies to:** any iteration that promotes a staging discovery to the canonical ledger via a `## Evidence Claim` — iter-11 (J-07 vcp_contraction h60), iter-12+ (J-08 combinations), and any future canonical "Proven"-badge write.
