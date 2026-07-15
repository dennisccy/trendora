# Phase goal-mcp-loop-iter-38 — Closure Verdict

**Phase:** goal-mcp-loop-iter-38 — Watchlist concentration X-ray (J-23 / B-204)
**Date:** 2026-07-15
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Context

J-23's own deliverable (the watchlist Concentration X-ray) is genuinely well-built and well-evidenced:
the pairwise correlation matrix, deterministic clusters, ENB headline+window, and sector/theme/setup
concentration are computed by one canonical `app.engine.concentration` helper, served additively on
`GET /api/watchlist`, and re-read verbatim by the page — confirmed by 24/24 fast backend tests, a live
production-seed E2E pass matching the closed-form 2-asset ENB formula to 10+ digits, and 13/15 browser
UI tests PASS (2 P2 tests SKIPPED for documented, test-plan-sanctioned reasons). All 6 UI visibility
artifacts exist with substantive, specific, non-vague content, and no backend-only-claim inconsistency
was found. **This is not the blocking issue.**

The block is the same recurring, precedented gap this project's own artifacts warn about by name. The
phase spec's NOTES section states: *"Systemic replay-gap flag (iter-33 + iter-36 both CLOSURE-FAILed on
it): a FULL iter routes through `run-phase.sh`, which has NO deterministic-replay lane. Run the closure
one-liner replay INLINE for the required-still-passing set OR follow iter-38 with a lean verify pass...
Durable fix... remains owed to the framework maintainer, not to this iteration."* The execution plan
(`runs/goal-mcp-loop-iter-38/plan.md`) repeats this, addressed explicitly to whichever agent owns
closure: *"do not let this iteration silently skip that re-verification and repeat the gap."* The
audit report itself (`docs/handoffs/goal-mcp-loop-iter-38-audit.md`) independently reaches the same
conclusion in its Executive Verdict and Recommended Next Step: the deterministic golden-replay of
J-01/J-02/J-03/J-05/J-10/J-13/J-20 **was not executed this iteration** ("services torn down;
smoke-200 + diff-intersection only"), and explicitly states this "MUST" happen via "an immediately
-following lean verify pass" before the required-still-passing set is marked green.

I independently traced this claim against the actual evidence in this pipeline rather than taking the
audit's flag at face value, and it holds up — see Blocking Issue #1 below, including a "designed vs.
executed" gap in QA's own test plan that is the closest thing to a smoking gun.

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-38-review.md`) | exists | PASS_WITH_NOTES |
| QA report (`reports/qa/goal-mcp-loop-iter-38-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-38-audit.md`) | exists | PASS_WITH_GAPS |

All three formal verdicts are at an acceptable label for closure per the standard rule (PASS /
PASS_WITH_NOTES / PASS WITH GAPS). As in iter-33 and iter-36, the block below comes from Step 3
(cross-reference validation), not from Step 1 — the standard gates alone would not stop this phase.

---

## UI Visibility Artifact Checks

`Frontend Present: yes` (confirmed in both `runs/goal-mcp-loop-iter-38/plan.md:81` and
`docs/phases/goal-mcp-loop-iter-38.md:10`).

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| `reports/phase-goal-mcp-loop-iter-38-implementation-summary.md` | yes | yes (89 lines) | yes — specific features, config values, explicit "Backend-Only Items: None" | OK |
| `reports/phase-goal-mcp-loop-iter-38-user-visible-changes.md` | yes | yes (43 lines) | yes — concrete live values (correlation −0.11, ENB "≈ 2.0", 50/50 sector split), explicit "Not Visible Yet" section | OK |
| `reports/phase-goal-mcp-loop-iter-38-ui-surface-map.md` | yes | yes (55 lines) | yes — 11-row table naming exact routes/components/`data-testid`s, explicit backend-to-UI feed-through tracing | OK |
| `reports/phase-goal-mcp-loop-iter-38-ui-test-plan.md` | yes | yes (500 lines) | yes — 15 test cases (UT-01–UT-15) with exact steps, exact expected copy/values | OK |
| `reports/phase-goal-mcp-loop-iter-38-ui-test-results.md` | yes | yes (155 lines) | yes — 13/15 executed with DOM-level evidence + screenshots; 2 P2 SKIPs with documented, test-plan-sanctioned reasons | OK |
| `reports/phase-goal-mcp-loop-iter-38-what-to-click.md` | yes | yes (87 lines) | yes — 8 numbered steps, each with a specific "Expect:" outcome | OK |

All 6 UI visibility artifacts exist and contain substantive, specific, non-placeholder content. The
`reports/phase-goal-mcp-loop-iter-38-ux-regression.md` optional artifact also exists and is substantive
(UX-REGRESSION-PASS). None of these are the source of the blocking finding below.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes, six bullet points with live numeric values
- [x] ui-surface-map has specific route/component entries — yes, full table with per-row "what to test"
- [x] ui-test-plan has specific steps with exact actions and expected results — yes
- [x] ui-test-results shows execution evidence — yes, 13/15 executed with screenshots/DOM evidence for
      the NEW capability (J-23); 2 P2 SKIPs are individually justified, not blanket "not run"
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 8 steps
- [ ] **implementation-summary / QA claims are consistent with the actual pipeline evidence — FAILS on
      one specific, material, DoD-named point: the "required-still-passing" re-verification claim.**

### The specific inconsistency (traced end-to-end, not just narrative-level)

The phase spec's DEFINITION OF DONE (`docs/phases/goal-mcp-loop-iter-38.md:84`) requires:

> Required-still-passing J-01, J-02, J-03, J-05, J-10, J-13, J-20 remain green, **re-verified by the
> deterministic golden-script replay run inline in this iteration (the closure one-liner) OR by an
> immediately-following lean verify pass** — so the iter-33 / iter-36 FULL-iter replay gap does not
> reopen.

QA's own generated functional test plan (`reports/qa/goal-mcp-loop-iter-38-test-plan.md:255-265`)
correctly operationalized this into a dedicated, explicit test case:

> **TC-17** — *"Execute the golden-script deterministic replay or run lean verify pass for each required
> journey... Pass criteria: J-01/J-02/J-03/J-05/J-10/J-13/J-20 all PASS in this iteration's replay run."*

This never happened. What the QA validation report (`reports/qa/goal-mcp-loop-iter-38-qa.md:105`)
actually recorded against TC-17 is:

> *"Regression check on /, /stocks, /evidence, /sectors, /research/factor-lab, /data all 200; watchlist
> add/remove untouched"* — marked **PASS**.

This is a bare HTTP-200 smoke check plus a diff-intersection argument, not a replay run, not a
lean-verify pass, and not evidence that "displayed numbers are correct" for any of the seven journeys —
which is this project's own anti-goal #3, quoted verbatim in the phase spec's Goal Mode Metadata: *"A
journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the
same as-of date — not merely that the page renders."* A 200 status code is exactly "the page renders,"
the specific thing anti-goal #3 says is insufficient. Marking TC-17 PASS against a pass criteria that
explicitly required "all PASS in this iteration's replay run" is the same class of overclaim that
CLOSURE-FAILed iter-36 (QA's "All live-verified ✓" was true for 6 of 8 journeys but not for the 2 that
mattered) and iter-33 (QA-designed replay test cases TC-24/25/26 were never executed, and the report
claimed a lean-verify lane that does not exist for a `Depth: full` iteration).

I independently confirmed the gap rather than trusting the audit's flag alone:
- The dispatched browser-qa test plan for this iteration (`ui-test-plan.md`, UT-01–UT-15) is scoped
  entirely to the new `/watchlist` X-ray section — none of the 15 UT cases navigate to `/stocks`,
  `/sectors`, `/evidence`, or `/research/factor-lab`, or assert any specific rendered value tied to
  J-01/J-02/J-03/J-05/J-10/J-13/J-20 (contrast with iter-35, where the dispatched UT-09/10/11/12 cases
  genuinely and directly exercised J-20/J-13/J-01/J-05 with real DOM assertions — that is what let
  iter-35 reach CLOSURE-PASS despite also lacking the literal replay-script artifact).
- `reports/phase-goal-mcp-loop-iter-38-ux-regression.md` does not mention J-01, J-02, J-03, J-05, J-10,
  J-13, or J-20 anywhere — its Regression Risk table only covers surfaces this iteration's own diff
  touches, not the required-still-passing set's own correctness.
- No `reports/phase-goal-mcp-loop-iter-38-regression-replay-results.md` file exists on disk (confirmed:
  `ls` returns "No such file or directory").
- The golden-script replay files this project already maintains for exactly this purpose are all
  present and ready to use: `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-02,J-03,J-05,J-10,J-13,
  J-20}.json` (confirmed present on disk, all pre-dating this iteration).
- Both the backend (`:8255`) and frontend (`:3255`) are currently stopped (health checks return `000`
  at the time of this check) — matching the audit's "services torn down" note — so neither a live replay
  nor a live spot-check was possible in the state this iteration was left in.
- Neither the reviewer nor QA caught the TC-17 designed-vs-executed gap; only the audit flagged it
  (correctly), but the audit did not treat it as blocking this closure gate — it recommended the fix
  happen "before the session marks the required-still-passing set green," which is precisely this gate's
  job to enforce, not to waive on the strength of a recommendation alone.

**Risk assessment (why this is fixable, not catastrophic):** actual product risk is plausibly low — this
iteration's diff only touches `app/engine/concentration.py` (new), `app/engine/watchlist_xray.py` (new),
`app/config.py` (additive `WatchlistCfg`/`WatchlistXrayCfg`, default-populated), `config.yaml` (additive
`watchlist:` block), `app/api/watchlist.py` (additive `xray` key only, `asof_date`/`entries[]` unchanged
per both the diff and the extended `test_api_watchlist.py`), and frontend files scoped to
`/watchlist`. None of J-01/J-02/J-03/J-05/J-10/J-13/J-20's own business-logic files were touched. But — as
this project's own phase spec explicitly states, and as iter-33's and iter-36's own closure verdicts
already established as binding precedent in this exact project — a diff-based low-risk argument is not a
substitute for the DoD's named live-or-replay check ("canonical-lane discipline," cited in this project's
own NOTES history at iter-13/20/22/31). The claim of completion is what fails here, not necessarily the
underlying journeys themselves.

---

## Blocking Issues

1. **DoD item "Required-still-passing... remain green, re-verified by the deterministic golden-script
   replay... OR by an immediately-following lean verify pass" was not satisfied for any of the seven
   journeys (J-01, J-02, J-03, J-05, J-10, J-13, J-20), and QA marked its own dedicated test case (TC-17)
   PASS despite the executed evidence not meeting that test case's own documented pass criteria.**

   This is the exact recurring gap this project's own artifacts (phase spec NOTES, execution plan,
   and the audit report) all independently name and warn against reopening — previously CLOSURE-FAILed
   at iter-33 and iter-36 for the same underlying reason (claimed-but-unexecuted re-verification of the
   required-still-passing set).

   **Remediation:** Run the deterministic replay against the golden scripts that already exist on disk
   for all seven journeys (confirmed present:
   `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-02,J-03,J-05,J-10,J-13,J-20}.json`). Services are
   currently stopped, so start them first:

   ```bash
   cd /home/dennis-chan/Git/trendora
   nohup scripts/start-backend.sh  > /tmp/iter38-backend.log  2>&1 &
   nohup scripts/start-frontend.sh > /tmp/iter38-frontend.log 2>&1 &
   # wait for both to come up
   until curl -s -o /dev/null -w '%{http_code}' http://localhost:8255/api/health | grep -q 200; do sleep 2; done
   until curl -s -o /dev/null -w '%{http_code}' http://localhost:3255/ | grep -q 200; do sleep 2; done

   python3 scripts/automation/lib/demo_runner.py --mode verify \
     --scripts-dir runs/goal-session-mcp-loop/journey-scripts \
     --journeys J-01,J-02,J-03,J-05,J-10,J-13,J-20 \
     --results reports/phase-goal-mcp-loop-iter-38-regression-replay-results.md \
     --evidence-dir reports/qa/goal-mcp-loop-iter-38-evidence \
     --base-url http://localhost:3255 \
     --phase-id goal-mcp-loop-iter-38 \
     --repo-root /home/dennis-chan/Git/trendora
   ```

   Exit code `0` = all seven pass cleanly — fold the result into
   `reports/phase-goal-mcp-loop-iter-38-ui-test-results.md` (or attach the new results file alongside it)
   so the DoD item has real, on-disk, falsifiable evidence, then correct
   `reports/qa/goal-mcp-loop-iter-38-qa.md`'s TC-17 row to cite that evidence instead of the smoke-200
   check. Exit code `5` (or any flagged journey) = dispatch browser-qa-agent to re-confirm the flagged
   journey(s) via the LLM lane and have the developer fix any genuine regression found before re-running
   this gate. Alternatively, per the DoD's own explicit "OR" clause, this may instead be closed by a
   dedicated lean verify-pass iteration (the iter-34 / iter-37 precedent in this same project) that runs
   the identical replay — either path is acceptable, but one of them must actually execute and produce
   on-disk evidence before this gate can re-run and pass.

   Re-run phase-closure-auditor once this evidence exists.

---

## Non-Blocking Notes

Already well-disclosed and reasonably triaged by review/audit; listed here only for completeness, not as
reasons for CLOSURE-FAIL:

- **B1** (review MINOR + audit GAP): `WatchlistXrayCfg` validator (`app/config.py:2352`) rejects only
  `min_overlap_days > corr_window_days`, but `min_overlap_days == corr_window_days` is also an
  unreachable floor by construction (`_returns` yields `len(bars)-1`). Shipped default (60/126) is
  unaffected; misconfiguration degrades honestly (NA, never a crash/fabrication). One-character fix
  (`>` → `>=`) recommended for a future pass, not blocking.
- **B2–B4** (audit OBSERVATIONs): over-conservative ENB eligibility for a hypothetical flat-price name
  (unreachable on real equity data); positional (not date-keyed) pairwise alignment, sound only for this
  product's single trading-calendar seed; canonical rows fetched twice per request (micro-perf only).
  None are shipped defects; all documented, not fixed, matching this project's own convention of not
  scope-creeping into non-shipped edge cases.
- **F1** (audit + ux-regression OBSERVATION): `enb_member_count` is computed and typed but has no render
  site — inert on the current 2-name watchlist, would matter on a larger list with exclusions. Already
  self-disclosed in `user-visible-changes.md`'s "Not Visible Yet" section and flagged by ux-regression as
  a future-pass item, not a closure blocker.
- **T1** (audit GAP): the 4 new `test_api_watchlist.py` tests rest on a single (reviewer-only) full-file
  run — dev deferred it (slow `loaded_engine` fixture reaped mid-setup) and QA collected it only
  partially. Mitigated by the auditor's own independent re-run of the two fast files (24/24 passed) plus
  the dev's live production-seed E2E and browser-qa UT-08/09 independently confirming the same additive
  behavior through different channels. Adequate per this project's iter-35 precedent for similarly
  single-sourced slow-fixture confirmations; not blocking.
- **T2** (review NOTE + audit OBSERVATION): no single composer-level test combines the exact "2 correlated
  + 1 independent" B-204 fixture to assert clusters and ENB together in one payload — both behaviors are
  covered separately. Optional, not blocking.
