## Iteration 0 — goal-mcp-loop-iter-0

**Date:** 2026-06-29T20:53:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Anti-goal violations: none (zero source diff — verify-only baseline)
- Seeded as UNKNOWN: J-01, J-02, J-03, J-04, J-05 (no browser evidence captured)

**Reasoning:** The baseline lean iteration's browser-QA lane never executed. telemetry.jsonl shows goal-decomposer → developer → reviewer → goal-evaluator with NO browser-qa-agent invocation; status.json reports browser_checks_run=false / current_step=dev_complete; reports/phase-goal-mcp-loop-iter-0-ui-test-results.md is absent and reports/qa/goal-mcp-loop-iter-0-evidence/ is empty (not even the goal-iter-lean.sh:392 SKIPPED stub was written). The iteration's sole deliverable — empirical J-01..J-05 verification — was therefore not produced, so all five journeys are UNKNOWN (I do not infer pass/fail from the developer's static code scan). git porcelain shows only untracked iteration artifacts (zero source diff) ⇒ no anti-goal could be violated; no coherence.md exists ⇒ no coherence veto (N/A on a no-op diff). Not REGRESSION (no prior-passing journey), not STALLED (iter 0, clear next step).

**Next-step recommendation:** Force a FULL iter-1 that stands up the read-side evidence path end to end — GET /api/evidence reading the certified-claims ledger via app.engine.ledger, the "Proven / Not yet proven" badge inline on /stocks + stock detail, the /evidence ledger page, and the Evidence nav entry — so that against the empty ledger every score honestly reads "Not yet proven" (structurally satisfies J-01, J-03, and J-05's ledger surface). Defer J-02 (drill into a PROVEN score) and J-04 (regime-conditioned PROVEN evidence) to a later iteration that proposes a `## Evidence Claim` and earns a referee PASS at the post-decompose gate (empty ledger ⇒ zero "Proven" badges by design). Full depth chosen because iter-1 introduces new public surfaces (nav section + page + cross-surface badges) needing ui-impact-analyst / ux-regression-reviewer / phase-closure gating, and because iter-0 captured no browser evidence the more robust full browser-QA lane should run next.

## Iteration 1 — goal-mcp-loop-iter-1

**Date:** 2026-06-29T22:37:16Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-01, J-03
- Newly partial: J-05 (ledger surface delivered; populated-claim linkback pending a certified claim)
- Newly failing: none
- Regressed: none
- Still deferred-unknown: J-02, J-04 (both need a referee-certified PASS claim)
- Anti-goal violations: none

**Reasoning:** The full pipeline closed the iter-0 browser-QA gap — status.json shows browser_checks_run=true / qa_complete, reports/phase-goal-mcp-loop-iter-1-ui-test-results.md exists (PASS, 12/15 PASS + 3 P2/P3 SKIP for un-automatable DevTools network-blocking states), and 4 distinct real screenshots back the claims. Verified visually: /stocks renders 120 rows each with three "Not yet proven" chips below intact grades+scores (J-01); MU detail shows 94.58/23.66/53.11 byte-identical to the leaderboard each with a "Not yet proven" chip (J-03, no recompute); /evidence is nav-reachable in 1 click with an honest empty state + all five claim fields (J-05 surface). The ledger file is absent and the resolver/badge are fail-safe (proven only on verdict.status==PASS + a named signal), so NOTHING reads "Proven" — anti-goals clean, COHERENCE-PASS. Not GOAL_ACHIEVED: J-02/J-04 deferred-unknown and J-05 only partial (steps 2-3 need a real claim). Not REGRESSION/STALLED (no prior pass to break; clear next step).

**Next-step recommendation:** Run iter-2 as the first CERTIFIED iteration (full): propose a narrow regime-conditioned `## Evidence Claim` that earns a referee PASS at the post-decompose gate, AND wire app.mcp.tools.verify_edge to stamp claim.signal (dev-handoff known gap — without it even a real PASS stays "Not yet proven"), AND build the J-02 drill panel (OOS test + controls + claim id/date). That one iteration advances J-02, completes J-05 end-to-end (populated row + linkback), and sets up J-04. Optionally fold in the coherence WARN (extract SCORE_SIGNALS to lib/evidence.ts).

## Iteration 2 — goal-mcp-loop-iter-2

**Date:** 2026-06-30T01:08:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none (browser-verified)
- Newly failing: none
- Regressed: none
- Backend milestone (not a journey-state change): first referee-certified claim landed (leadership_score PASS); /api/evidence serves proven_signals.leadership_score.proven==true
- Still unknown (targeted but unverified): J-02 (code shipped + gate PASS + API proven, but browser lane SKIPPED)
- Still partial: J-05 (data now exists; populated-row + linkback browser proof still missing)
- Still deferred-unknown: J-04 (out of scope iter-2)
- Carried passing (NOT re-verified — browser lane skipped): J-01, J-03
- Anti-goal violations: none (secret scan clean; no return/buy-sell language; no second computation path; determinism preserved; claim survived sealed holdout + SPY control + bonferroni)

**Reasoning:** The data half genuinely succeeded — gate-post-decompose.json shows blocked=false with a single PASS, certified-claims.jsonl holds the first entry (holdout 279 dates, in-sample 828, SPY control n=1137, bonferroni, p=0.0004998<0.05, signal=leadership_score), and QA's curl (TC-13) confirms /api/evidence serves it byte-identical. Coherence=PASS, review=PASS, anti-goals clean. BUT the user-facing journeys were never browser-verified: status.json browser_checks_run=false, both reports/phase-...-ui-test-results.md and reports/qa/...-qa.md SKIPPED every browser test (frontend stuck on 'Checking backend...'), the only screenshot TC-01-stocks-page.png shows an empty leaderboard (a harness frontend->backend connectivity failure, not a code regression — next build + tsc + units all green), and no audit handoff was produced. Per the iter-1 lesson embedded in this very spec, a ledger row + green build/units/API does NOT equal a browser-proven badge flip. So J-02 stays unknown, J-05 stays partial, and J-01/J-03 are carried (not re-verified). Not GOAL_ACHIEVED (targets unverified). Not REGRESSION (no prior-pass broke; empty leaderboard is connectivity, not code). Not STALLED (clear, fixable next step; real backend progress). ESCALATE doesn't fit (already full). CONTINUE, full.

**Next-step recommendation:** iter-3 = full browser-verification pass of already-shipped code (do NOT rebuild dev work). (1) Fix the harness root cause — frontend :3255 can't reach backend :8255 ('Checking backend...' / empty leaderboard / no regime / no themes): service-start order, API base URL, or health-proxy. (2) Browser-verify J-02 (proof drill-down matches /api/evidence), J-05 (populated row + linkback round-trip), and the Leadership badge flip to 'Proven' on /stocks + detail with Entry Quality + Risk still 'Not yet proven' (J-01/J-03). Treat browser_checks_run=false + all-SKIP results as a hard verification gap, never as a pass.

## Iteration 3 — goal-mcp-loop-iter-3

**Date:** 2026-06-30T02:42:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-02 (was unknown), J-05 (was partial)
- Re-confirmed fresh (after the iter-2 verification gap): J-01, J-03
- Newly failing: none
- Regressed: none
- Still unknown (correctly out of scope): J-04 (no regime-scoped certified claim exists yet)
- Anti-goal violations: none (zero apps/ diff; secret scan clean; no buy/sell/price/alpha language; determinism/no-lookahead untouched; only Leadership reads "Proven", backed by the certified leadership_score PASS)

**Reasoning:** The iter-2 hard verification gap is closed — the browser-QA lane actually ran this time (status.json browser_checks_run=true, current_step=qa_complete; reports/phase-goal-mcp-loop-iter-3-ui-test-results.md = PASS 16/16, 0 skipped; non-empty evidence dir with real captures). The fix was operational and minimal exactly as the iter-2 evaluator predicted: scripts/start-frontend.sh switched `next dev` -> stamp-guarded `next start`, with ZERO apps/ source diff (git diff --stat HEAD: only the one script + two journey-script JSONs + telemetry). Verified visually: UT-02-result.png is a real populated /stocks (120/120 rows, health "Ready") with Leadership green "Proven" chips and Entry Quality + Risk muted "Not yet proven" (J-01/J-03); UT-06-result.png shows the same on /stocks/MU with values byte-identical to the leaderboard; UT-12-evidence-page.png shows the fully-populated leadership_score PASS row with all five fields + the "Backs: Stocks leaderboard ->" link, and UT-14 confirms that linkback round-trips to the populated leaderboard (J-05). J-02: the detail "Why proven?" toggle + the in-panel "View backing evidence row ->" link (href /evidence#signal-leadership_score, confirmed navigating in UT-09) + the panel's exact OOS values (PASS/+6.36%/p=0.0004998/n=12,297/vs SPY/registered 2026-06-30) rendering byte-identically on /evidence -> passing, though I note the panel-named screenshots (UT-07/UT-08/TC-05/UT-16) are byte-identical full-page-top frames that stop above the expanded panel (it renders below the fold; confirmed via DOM + /evidence mirror + linkback, not via a pixel capture of the panel itself). Coherence=PASS (one op script + two test JSONs; no IA/data-contract drift) -> no structural veto. Not GOAL_ACHIEVED: J-04 is a Must-have journey still unknown (never attempted; no regime-scoped certified claim). Not REGRESSION (no prior-pass broke). Not STALLED (clear next step + real progress). Minor process gap: the post-QA audit handoff is absent (status stops at qa_complete) — does not change journey evidence.

**Next-step recommendation:** iter-4 (full) = tackle J-04, the sole remaining Must-have journey. Spec MUST include a narrow, regime-conditioned ## Evidence Claim (regime-scoped cohort) so the post-decompose referee gate certifies it BEFORE code; prefer a narrow regime slice over a broad data-mined one. On PASS, surface the regime-conditioned evidence labeled with the regime it holds in (Dashboard regime + Evidence/Research), browser-verify it, and GOAL_ACHIEVED becomes reachable. A gate FAIL/INSUFFICIENT correctly blocks — propose a different narrow cohort next. Carry: produce the auditor handoff next full run; add `tsx` frontend devDependency (reviewer NOTE); browser-QA must scroll below-the-fold disclosures into frame before capturing.

## Iteration 4 — goal-mcp-loop-iter-4

**Date:** 2026-06-30T04:05:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly partial: J-04 (was unknown — regime-conditioned-evidence feature delivered, gate-certified, and QA-lane-verified, but the canonical browser-qa lane SKIPPED so session-standard verification is incomplete)
- Re-confirmed fresh (pixel): J-05 (TC-03 shows the leadership row byte-unchanged + new regime row didn't break the list)
- Carried passing (NO fresh iter-4 pixel; code paths untouched + QA-textual reconfirm): J-01, J-03 (/stocks), J-02 (/stocks/{ticker})
- Newly failing: none
- Regressed: none
- Backend milestone (not a journey-state change): session's first REGIME-CONDITIONED edge certified — gate-post-decompose.json blocked=false, certified-claims.jsonl 2nd entry = Breakout-watch x Risk-on event-study PASS (holdout +6.12% vs SPY, p=0.0004998 < alpha/2=0.025, 107 holdout dates / 277 in-sample, signal=null)
- Anti-goal violations: none (zero apps/backend/app diff; secret scan clean; no buy/sell/return-promise language — only a guard comment; proven_signals unit-tested to stay {leadership_score} only; determinism/no-lookahead untouched; displayed numbers byte-identical to the ledger)

**Reasoning:** The feature half genuinely succeeded and I personally inspected the proof — TC-01 (Dashboard Risk-on 76.05 + "See evidence proven in this regime ->" affordance) and TC-03 (/evidence "Regime: Risk-on" Breakout-watch row, +6.12% vs SPY, p=0.0004998 < alpha/2=0.025, registered 2026-06-30, "Backs: Research event-study lab ->", values byte-identical to certified-claims.jsonl line 2; leadership row byte-unchanged with "Backs: Stocks leaderboard ->"). Gate PASS, coherence=PASS, review=PASS, QA=PASS, anti-goals clean, diff surgical and frontend-only. BUT GOAL_ACHIEVED is withheld on a verification-integrity gap: the canonical browser-qa-agent lane reported all 11 SKIP ("frontend not running" — a stale next-server held :3255, per the dev handoff's Known Issues), which is the exact iter-0/iter-2 pattern the spec's OWN embedded lesson designates a HARD verification gap; the two real screenshots come from the QA agent's PARALLEL lane (TC-* naming), not the canonical lane; J-01/J-02/J-03 have NO fresh iter-4 pixels (only QA-textual TC-07/TC-08 + untouched code); and the spec-required post-QA audit handoff is ABSENT (current_step=qa_complete — same iter-3 gap the iter-4 spec explicitly required closing). For the terminal success verdict that is too thin a base. Not REGRESSION (no prior-pass broke; J-05 pixel-verified unchanged; J-01/J-02/J-03 paths untouched; no critical anti-goal). Not STALLED (real progress; concrete cheap next step). ESCALATE doesn't apply (already full). CONTINUE, full.

**Next-step recommendation:** iter-5 (full) = the final decisive verification pass, NO new feature code beyond a harness fix. (1) Free :3255 before the browser-qa lane binds (kill orphan next-server; start-frontend.sh lacks dev.sh's pre-bind fuser -k — this is why the canonical lane SKIPPED). (2) Capture fresh canonical UT-* screenshots for ALL FIVE journeys: J-04 (Dashboard affordance -> /evidence regime row scrolled into frame), J-05 (leadership linkback round-trip), J-01/J-03 (/stocks all-three-status), J-02 (/stocks/{ticker} drill-down). (3) Produce the post-QA audit handoff (docs/handoffs/goal-mcp-loop-iter-5-audit.md) — the audit stage has stopped at qa_complete twice now. On a clean full run all five journeys go green through the session-standard lane and GOAL_ACHIEVED is reachable.

## Iteration 5 — goal-mcp-loop-iter-5

**Date:** 2026-06-30T05:30:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: <none — J-04 held at partial>
- Newly failing: <none>
- Regressed: <none — no product/journey regression; zero apps/ diff>
- Anti-goal violations: <none — anti_goal_violations remains []>

**Reasoning:** The ONE code deliverable landed and is correct — `scripts/start-frontend.sh` now frees `$FRONTEND_PORT` before bind (review PASS, dev's live error-case test serves the fresh bundle; git diff = only that script + telemetry, zero `apps/` diff). BUT the two gating verification deliverables iter-5 existed to produce are BOTH absent: the canonical `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md` does NOT exist (broad search confirms) and `docs/handoffs/goal-mcp-loop-iter-5-audit.md` does NOT exist; status.json is stuck at `qa_complete`/`next_action: auditor`. The screenshots that exist (UT-04/05/07/09) are from the QA agent's PARALLEL Chrome MCP lane — explicitly disqualified by the session standard (QA report TC-11 itself marks the canonical lane "PENDING") — and are incomplete on their own terms: UT-07≡UT-09 are byte-identical duplicates (md5 cfe695e8…) so J-05's round-trip wasn't captured, and UT-05 shows only the MU score cards at a historical as-of, not the J-02 proof drill-down. Engine.log L402-413 reveals the REAL root cause (not the port the dev fixed): the post-dev parallel Branch-UI chain aborted at `ui-test-design` ("user-visible-changes report not found" though ui-impact reported writing it) so the canonical browser-qa-agent lane + ux-regression + closure never ran, and the `invalid step 'post_dev_parallel_complete'` bug (also iter-4 L343) defeated the sequential-retry fallback so the auditor never ran. Cannot GOAL_ACHIEVED: J-04 stays `partial`, gating artifacts missing. Not REGRESSION (nothing passing→failing; harness-only). Not STALLED (a precise, named, actionable harness fix is now identified).

**Next-step recommendation:** iter-6 (FULL — auditor only runs in the full pipeline). ONE allowed code change, in the HARNESS not `apps/`: fix the post-dev Branch-UI chain so the canonical lane actually runs — (a) make `ui-test-design-phase.sh` find the `phase-*-user-visible-changes.md` that `ui-impact-phase.sh` writes (path/timing mismatch at engine.log L402 vs L406), and (b) fix the `invalid step 'post_dev_parallel_complete'` update_status call (L412-413) so the sequential-retry fallback re-runs the aborted Branch-UI steps (browser-qa-agent, ux-regression, closure) AND the auditor. DoD for iter-6: `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` exists with non-SKIP UT-* for all five journeys (J-04 → passing; J-02 EXPANDED proof panel scrolled into frame; J-05 round-trip as a DISTINCT screenshot, not a dup of /evidence) AND `docs/handoffs/goal-mcp-loop-iter-6-audit.md` exists. The keep-`apps/`-frozen + port-free fix from iter-5 stand. ESCALATION FLAG: this is the 2nd consecutive canonical-lane miss and 3rd consecutive absent auditor — if iter-6 ALSO fails to run the canonical lane + auditor, treat the session as STALLED (harness needs hands-on human repair, not another loop).

## Iteration 6 — goal-mcp-loop-iter-6

**Date:** 2026-06-30T06:30:00Z
**Verdict:** GOAL_ACHIEVED
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-04 (partial → passing — first canonical pass; regime-conditioned evidence)
- Re-verified passing on the canonical lane (last canonical pixel was iter-3/iter-4): J-01, J-02, J-03, J-05
- Newly failing: none
- Regressed: none
- Anti-goal violations: none

**Reasoning:** The iter-5 ESCALATION FLAG is fully resolved. Iter-6 fixed the four named harness defects and, as direct proof, the CANONICAL browser-qa-agent lane ran end-to-end (engine.log L468-483: ui-impact → ui-test-design → browser-qa "Done. Report: …phase-goal-mcp-loop-iter-6-ui-test-results.md", PASS 5/5) AND the auditor ran (engine.log L515 `[audit attempt 1/3]` → audit handoff PASS_WITH_GAPS) — both for the first time in 2-3 iters, with no `invalid step 'post_dev_parallel_complete'` abort and no ui-test-design "report not found" abort (contrast iter-4 L334-343, iter-5 L405-413). All five Must-have journeys pass on the canonical lane; J-04 flips partial→passing. I personally inspected UT-J-04-dashboard.png (Risk-on 76.05 + "See evidence proven in this regime →" affordance), UT-J-04-regime-evidence.png ("Regime: Risk-on" claim scrolled into frame), UT-J-01-stocks-badges.png (120/120, every score has a status), and UT-J-02-proof-panel.png (score cards). Zero `apps/` diff (git-verified), coherence COHERENCE-PASS, ledger unchanged at 2 referee-certified PASS claims, displayed numbers byte-match certified-claims.jsonl (+6.36%/+6.12%, p=0.0004998, cohorts 12297/4720, dates 2026-06-30); all seven anti-goals upheld. Corroboration: Review PASS, QA PASS (60/60 evals), Closure CLOSURE-PASS, Audit PASS_WITH_GAPS "Proceed". Two non-blocking gaps remain (B2: `browser_checks_run` flag never wired to true — judged on the demonstrated canonical lane per instructions, not the stale flag; T1: J-02 inline expanded-panel below-the-fold — content corroborated via /evidence row + ledger byte-match + frozen iter-3 pixel, so functionally passing).

**Next-step recommendation:** Halt — goal achieved. Every goal.md success criterion is met (visible evidence status on every score, auditable proof behind each "proven" claim, honest "Not yet proven" marking, regime-conditioned evidence, zero uncertified edges — gate-enforced, 2 PASS claims). Optional future maintenance (NOT required): one lean harness/QA pass could close the two carry-forwards — wire `browser_checks_run=true` when the fanout produces a non-SKIP ui-test-results.md (B2), and scroll the J-02 expanded proof panel into frame before capture (T1).

## Iteration 7 — goal-mcp-loop-iter-7

**Date:** 2026-06-30T19:00:00Z
**Verdict:** GOAL_ACHIEVED
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none (all five already passing at iter-6)
- Re-confirmed passing on the canonical lane: J-01, J-02, J-03, J-04, J-05
- Newly failing: none
- Regressed: none
- Anti-goal violations: none

**Reasoning:** Verify-only re-confirmation, exactly as the spec mandated. The canonical browser-qa lane ran and returned PASS 5/5 (reports/phase-goal-mcp-loop-iter-7-ui-test-results.md, 0 skipped) with real freshly-captured screenshots. I personally inspected one+ pixel per journey: UT-J-01-result.png (md5 617da05) — /stocks 120/120 rows, every Leadership "Proven", every Entry Quality + Risk "Not yet proven", Regime "Risk-on 76.05" (J-01 + J-03); UT-J-02-result.png (md5 80c7cdd) — /stocks/MU three score cards, expanded panel below the fold (recurring T1) but replay asserted the panel texts, corroborated by the /evidence row + ledger byte-match + frozen iter-3 pixel; UT-J-04-dashboard.png (md5 0a0c589) — Regime affordance; UT-J-04-result.png ≡ UT-J-05-result.png (md5 cfe695e8) — /evidence ledger with both PASS claims, regime-labeled, backing links, values byte-matching certified-claims.jsonl (+6.36%/+6.12%, p=0.0004998). git-verified ZERO apps/ diff (tracked + untracked both empty); only non-product changes (J-02 test script, telemetry, session.json). Ledger unchanged at exactly 2 referee-certified PASS entries; 13/13 evidence/byte-match unit tests green; coherence COHERENCE-PASS (not COHERENCE-FAIL); review PASS; all seven anti-goals upheld (only Leadership reads "Proven", backed by the certified claim; no buy/sell/return language; displayed numbers correct; both claims survived the referee; no new uncertified edge). AUTO:journeys block empty — no new auto-proposed scope. Every goal.md success criterion is met with positive evidence and no open FAILING/PARTIAL journey. Not REGRESSION (nothing passing→failing), not STALLED (terminal success, not an unproductive loop), not CONTINUE/ESCALATE (no remaining tractable scope and no structural veto). GOAL_ACHIEVED.

**Next-step recommendation:** Halt — goal achieved. Optional non-blocking maintenance only (NOT required): scroll the J-02 expanded proof panel into frame (T1), and capture J-05's step-3 round-trip as a distinct landed-on /stocks frame instead of reusing the /evidence list image (UT-J-04-result and UT-J-05-result are byte-identical this iteration). Both are corroborated and do not gate the goal.

## Iteration 8 — goal-mcp-loop-iter-8

**Date:** 2026-06-30T22:12:00Z
**Verdict:** GOAL_ACHIEVED
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-06 (vcp_contraction top-decile certified edge on the Research factor lab + a 4th /evidence claim row)
- Newly failing: none
- Regressed: none
- Anti-goal violations: none (all seven upheld; the rejected ma_stack cohort is the only FAIL ledger entry and correctly reads "Not yet proven" on both surfaces)

**Reasoning:** Verified the full chain independently rather than trusting handoffs. The gate certified vcp_contraction PASS as certified-claims.jsonl line 4 (holdout +0.0333, p=0.011494 < required_p 0.0125, divisor 4, no `signal` key). git diff confirms ZERO apps/backend/app/** change — only apps/frontend/* + tests — so the engine/referee/`/api/evidence` shape and determinism/no-lookahead are untouched. Personally inspected UT-05 (/evidence: all four rows, vcp PASS +3.33% byte-matching the ledger, honest "Out-of-sample edge" subtitle, "Backs: Research factor lab →"), UT-15 (/stocks: 120/120 rows, Leadership "Proven", Entry Quality + Risk "Not yet proven", hasVcp=false — no inline badge), UT-16 (MU detail with the drill-down DOM-asserted), and the factor-lab frames (leadership "Proven", ma_stack/others "Not yet proven"). Coherence is COHERENCE-PASS. All six Must-have journeys pass; secret-scan of the diff is clean.

**Next-step recommendation:** Halt — goal achieved. J-01…J-06 all green and the AUTO:journeys block carries no further unbuilt scope. If the continuous-improvement proposer extends docs/goal.md again, dispatch lean for a verify-only re-confirmation; escalate to full only if the new journey ships a referee-gated "proven" claim or touches the shared evidence resolver / a new public-surface badge.
