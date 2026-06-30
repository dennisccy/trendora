# goal-mcp-loop-iter-6 Audit Report

**Date:** 2026-06-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase's primary goal is **achieved**: the four named harness defects are fixed exactly as
specified, and as a direct, verifiable result the canonical `browser-qa-agent` lane ran this
iteration (engine.log `05:45:42 → 05:51:18`, "frontend is ready", canonical `…-ui-test-results.md`
produced) **and** the auditor is running now — both for the first time in 2–3 iterations, averting
the spec's STALL escalation. Zero `apps/` diff is git-verified, the eval suite is green (60/0), all
five journeys pass on the canonical lane with J-04 flipping `partial → passing`, and the displayed
numbers byte-match the certified-claims ledger. Two evidence-fidelity gaps remain (the J-02 expanded
proof-panel screenshot is not scrolled into frame — the recurring iter-3 below-the-fold miss; and the
informational `browser_checks_run` status flag stays `false`), but neither compromises the goal or the
product, and both are documented below.

---

## 2. Findings

### Backend / Harness Findings

**B1 — OBSERVATION (verified): All four named defects fixed exactly as specified; same-run levers demonstrably effective.**
Verified each fix against the diff and confirmed effect against `runs/goal-session-mcp-loop/engine.log`:
- *Defect #3 (load-bearing):* `lib/verdicts.py:112` adds `POST_DEV_PARALLEL_COMPLETE = "post_dev_parallel_complete"` to the `PhaseStep` enum. iter-4 (`engine.log:343`) and iter-5 (`:412`) both died on `Error: invalid step 'post_dev_parallel_complete'`; iter-6 has no such abort and the auditor is executing (`:515` `[audit attempt 1/3]`). The fix worked this run because `verdicts.py` is a fresh subprocess per call, exactly as the spec predicted.
- *Defect #1 (load-bearing):* `ui-impact-phase.sh` (guard ~L107–118) now asserts `-s "$USER_VISIBLE" && -s "$UI_SURFACE_MAP"` on rc==0, else writes stubs + `exit 1`. iter-5 (`engine.log:402–408`) showed the phantom "Done." → ui-test-design abort; iter-6 (`:471–476`) ran ui-impact → ui-test-design → browser-qa to completion in-fanout.
- *Defect #2:* `ui-test-design-phase.sh` (guard ~L120–131) mirrors the same `-s` post-condition for `$UI_TEST_PLAN`/`$WHAT_TO_CLICK`, correctly placed **after** the signal-exit guard and the rc≠0 branch (anti-pattern #20 signal semantics preserved).
- *Defect #4 (next-run robustness):* `run-phase.sh:645–651` gates each `SKIP_*=true` on its artifact existing (`-s`), and `:411–415` adds the `post_dev_parallel_complete|browser_qa_complete` resume arm. Correct; its full effect lands on the next dispatch (mid-run parent re-read is unreliable, as the spec itself notes).

**B2 — GAP (gap): `browser_checks_run` status flag remains `false` though the canonical lane ran.**
`runs/goal-mcp-loop-iter-6/status.json` shows `"browser_checks_run": false` even though the canonical
browser-qa lane genuinely ran (engine.log `05:45–05:51`; `…-ui-test-results.md` with 5/5 PASS). Root
cause: the field is initialized `false` in `lib/common.sh:242` and is **never set to `true` by any
harness path** — a repo-wide grep finds no setter and no consumer/gate. The fanout's browser-qa produces
the canonical results, but the only code that would have flipped the flag is the *sequential* Step 6,
which was correctly skipped (`engine.log:502` "Step 6/11 — Browser QA: skipped"). The literal DoD wording
"`browser_checks_run=true`" is therefore unmet **at the status-field level**, while the substantive
requirement (browser checks actually ran via the canonical lane) is fully met by the authoritative
artifact + engine.log. **No fix applied:** the field has no downstream consumer (nothing fails because of
it), the true root cause is a separate, unnamed harness-wiring defect outside this iteration's four-defect
scope, and overwriting the boolean would *mask* that gap rather than surface it honestly. Flagged for the
next harness iteration: have the fanout browser-qa path (or the post-fanout checkpoint) set
`browser_checks_run=true` when `…-ui-test-results.md` exists and is non-SKIP.

**B3 — OBSERVATION (observation): 14 unrelated automation scripts show mode-only (chmod) changes.**
`git status` lists ~14 extra `scripts/automation/*.sh` as modified (e.g. `qa-phase.sh`, `dev-phase.sh`,
`phase-audit.sh`), but `git diff` confirms these are **mode-only** (`old mode 100644 → new mode 100755`),
0 insertions/0 deletions. No content scope creep: the only content changes are the five files in
`changed_files` (`verdicts.py` +1, `run-evals.sh` +54, `run-phase.sh` ±16, `ui-impact-phase.sh` +12,
`ui-test-design-phase.sh` +12). The chmod noise is benign but technically outside the "four named defects"
boundary; harmless.

**B4 — OBSERVATION (verified): scope, determinism, and anti-goal constraints all hold.**
`git diff --name-only -- apps/` is empty and `git status -- apps/` is empty → **zero `apps/` diff**
confirmed. The iter-5 `start-frontend.sh` port-free fix is retained (no diff). The certified-claims
ledger (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`) holds **exactly 2 PASS entries** —
unchanged, as required (no `## Evidence Claim` block → post-decompose gate auto-passes). No new claim,
factor, or ledger entry introduced.

### Frontend Findings

**F1 — N/A (verified): frontend frozen and exercised verbatim.**
No `apps/frontend/**` change. The existing evidence UI (`/stocks`, `/stocks/{ticker}` proof panel,
`/evidence` ledger, Dashboard regime affordance) was driven as-is by the canonical lane. Direct screenshot
inspection (`UT-J-04-regime-evidence.png`, `UT-J-02-proof-panel.png`) confirms the real Trendora UI with
live data and the "Research-only · decision support · no orders" header — no order/return/price-target
copy (decision-quality anti-goal upheld).

### Test / Evidence Findings

**T1 — GAP (gap): J-02 expanded proof-panel screenshot is not scrolled into frame (recurring iter-3 below-the-fold miss).**
`reports/qa/goal-mcp-loop-iter-6-evidence/UT-J-02-proof-panel.png` is a genuine, unique capture of
`/stocks/MU`, but the frame ends at the three score cards (Leadership 94.58 "Proven", Entry Quality 23.66
+ Risk 53.11 "Not yet proven"); the **expanded** proof panel (OOS test, control vs SPY, certified-claim
id, registration date) the DoD explicitly requires "scrolled into frame" is **not visible** — exactly the
standing below-the-fold lesson the spec called out. The `…-ui-test-results.md` narrative *claims* the
expanded content ("Sealed holdout cohort: 12,297 observations", "+6.36% vs SPY", "leadership_score ·
registered 2026-06-30"). Crucially, that narrative is **corroborated**: 12,297 byte-matches `cohort_n:
12297` in the ledger and +6.36%/p=0.0004998 byte-match `holdout_edge: 0.06359…`/`p_value: 0.0004998` — so
J-02 genuinely passes functionally and was not fabricated; only the *visual evidence framing* fell short.
**No fix applied:** re-capturing is the `browser-qa-agent`'s domain (not a surgical source fix), and
driving the browser against the still-live frontend mid-pipeline risks the corrupt-`.next` hazard
(anti-pattern #20) the dev deliberately avoided. Recommend the next canonical-lane run scroll the expanded
J-02 panel into frame before capture.

**T2 — OBSERVATION (observation): cross-journey screenshot byte-duplication.**
md5 analysis: `UT-J-01-stocks-badges.png` == `UT-J-03-not-yet-proven.png` == `UT-J-05-evidence-roundtrip.png`
(all `/stocks`); `UT-J-04-regime-evidence.png` == `UT-J-05-evidence-ledger.png` (both `/evidence`);
`UT-J-04-dashboard.png` == `frontend-loads.png` (both Dashboard). The **literal** DoD requirements are
nonetheless met: the J-05 round-trip frame (`617da05…`, `/stocks` backing surface) is **distinct** from the
`/evidence` list frame (`cfe695e…`), satisfying "not a byte-duplicate of the /evidence list frame"; and the
J-02 panel capture is unique. The duplication reflects that several journeys legitimately share a surface
(`/stocks` backs J-01/J-03 and the leadership_score claim's linkback; `/evidence` is both the J-04 regime
view and the J-05 list). Capture hygiene is weak (frames reused across journeys), but no DoD clause is
violated.

**T3 — OBSERVATION (verified): eval suite green; new TDD tests are sound.**
Re-ran `./scripts/automation/run-evals.sh` → **60 pass, 0 fail, exit 0**. The three new tests
(`run-evals.sh:148–204`) cover: (1) `validate-step post_dev_parallel_complete` exits 0; (2) structural
grep that both phase scripts carry the rc==0 `-s` guard for both outputs; (3) a behavioral exercise of the
real `write_failed_artifact_stub` (writes a stub when absent, no-ops when present). The structural test (2)
is static rather than an end-to-end script invocation, but combined with the behavioral test (3) and the
dev's out-of-suite guard-byte execution it is adequate.

---

## 3. Domain Assessment

The decision-quality domain is correct and honestly surfaced. The `/evidence` ledger (verified by direct
screenshot + raw `certified-claims.jsonl` inspection) presents exactly two referee-certified claims, each
**out-of-sample** (sealed holdout), **control-beating** (vs SPY), and **multiple-testing-corrected**
(Bonferroni deflation, divisor 1 for the single leadership_score trial, divisor 2 for the 2-trial
Breakout-watch event-study). Displayed values byte-match the engine: `+6.36%`/`+6.12%`,
`p=0.0004998`, `alpha/1=0.05`/`alpha/2=0.025`, `12,297`/`4,720` cohorts. No-lookahead is respected —
`in_sample_edge` (0.0035 / 0.0004) is cleanly separated from the sealed `holdout_edge` (0.0636 / 0.0612),
and `/stocks/MU` shows forward returns as `NA` "where not enough post-date bars exist yet (never
fabricated)." Everything not backed by a passing certified claim reads "Not yet proven" (Entry Quality,
Risk). J-04's regime-conditioning is real: the Breakout-watch claim is scoped to and labeled "Regime:
Risk-on", and the Dashboard's "See evidence proven in this regime →" affordance links to it. All five
critical anti-goals hold; no order/return/price-target language appears anywhere. Because this is a
harness-only iteration with zero `apps/` diff, none of this domain logic could have regressed.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. The harness deliverable is correct and exactly scoped; the two remaining gaps (T1 screenshot framing, B2 status flag) are not surgically fixable without re-driving the browser against the live pipeline or masking a separate harness-wiring gap. Both are documented as GAPs for the next iteration. |

---

## 5. Recommended Next Step

**Proceed.** This iteration accomplished its sole purpose — repairing the verification pipeline so the
canonical `browser-qa-agent` lane and the auditor both run — and the evidence (engine.log, the canonical
`…-ui-test-results.md`, the auditor executing now) confirms it end-to-end. The spec's STALL escalation is
averted. The goal-evaluator can mark J-04 `passing` and the four required journeys green on the basis of
the canonical lane, grounded in ledger-byte-matched values. Two non-blocking carry-forwards for the **next
harness iteration** (not this one): (1) wire `browser_checks_run=true` when the fanout browser-qa produces
a non-SKIP `…-ui-test-results.md`, so status.json stops under-reporting (B2); and (2) have the canonical
lane scroll the J-02 expanded proof panel into frame before capture, closing the recurring iter-3
below-the-fold evidence gap (T1). Neither warrants reopening iter-6.
