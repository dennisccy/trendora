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
