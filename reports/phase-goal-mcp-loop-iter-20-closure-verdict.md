# Phase goal-mcp-loop-iter-20 — Closure Verdict

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-08
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-20-review.md`) | exists | PASS |
| QA report (`reports/qa/goal-mcp-loop-iter-20-qa.md`) | exists | PASS (verdict line reads PASS; see Blocking Issue #3 — content partially unreliable) |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-20-audit.md`) | exists | PASS_WITH_GAPS |

Step 1 does not trigger an automatic fail — all three gates carry an accepted verdict value. The failure below comes from Step 2/3/4 (UI evidence + browser-QA-execution guard), not from a missing/failing standard gate.

---

## UI Visibility Artifact Checks

`Frontend Present: yes` (per `runs/goal-mcp-loop-iter-20/plan.md:37` and `docs/phases/goal-mcp-loop-iter-20.md:10`).

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes (78 lines) | yes — specific features/behavior changes named | OK |
| user-visible-changes.md | yes | yes (43 lines) | yes — specific before/after copy, colors, capabilities | OK |
| ui-surface-map.md | yes | yes (63 lines) | yes — named routes, components, testids, line numbers | OK |
| ui-test-plan.md | yes | yes (538 lines) | yes — 22 cases, exact steps/hex/rgb/copy expectations | OK |
| ui-test-results.md | yes | yes (161 lines) | yes, well-formed (not placeholder text) — **but 0/22 executed, 22/22 SKIPPED** | PRESENT, ZERO EXECUTION EVIDENCE (see Blocking Issue #1) |
| what-to-click.md | yes | yes (67 lines) | yes — 10 numbered steps with exact expected outcomes | OK |

Five of six artifacts are genuinely well-formed and specific. `ui-test-results.md` is not vague or templated — every row is filled in with real expected-vs-actual text — but its content is a blanket SKIP with no browser session ever opened. That is a process/evidence failure, not an artifact-quality failure, which is why it is called out separately below rather than marked MISSING/VAGUE.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes (heatmap legend split, tooltip wording, widened Fetch scope shown via the existing symbol counter, Expand option removal)
- [x] ui-surface-map has specific route/component entries — yes (`/data`, `JobForm`, `AvailabilityHeatmap`, `availability-legend-density`/`-snapshot` testids)
- [x] ui-test-plan has specific steps with exact actions and expected results — yes (exact hex/rgb values, exact copy strings, exact preconditions)
- [ ] **ui-test-results shows execution evidence (or SKIPPED with documented reason) — NOT MET.** All 22 cases are SKIPPED. A proximate cause is logged ("frontend not running," confirmed by a `curl → 000` precondition check), but there is no documentation anywhere accepting this as an intentional, adequate substitute for this phase — the opposite: both the audit (finding T3) and the ux-regression review (verdict `UX-REGRESSION-WARN`, recommendation #1) explicitly flag the SKIP as an open gap and recommend re-dispatching browser-qa-agent before treating J-13 as closed.
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes (10 steps, well above the 3-step floor)
- [ ] **implementation-summary claims are consistent with ui-test-results evidence — NOT MET.** `implementation-summary.md` states "Incomplete Items: None from this iteration's plan... every item in the phase's checklist was implemented," treating the phase as fully verified, while the canonical browser-QA lane executed 0 of 22 checks. Separately, `reports/qa/goal-mcp-loop-iter-20-qa.md`'s "Browser Checks" section asserts "Frontend is running and responsive" / "Frontend running at http://localhost:3255 as expected" from a curl probe, while `reports/phase-goal-mcp-loop-iter-20-ui-test-results.md` (browser-qa-agent, same phase, same day) logs that exact same kind of curl probe returning `000` (connection failure) on both `:3255` and `:8255`. These two required pipeline artifacts directly disagree about service reachability.

---

## Live Environment Re-Check (performed now, at closure time)

- `curl http://localhost:3255` → `000` (unreachable)
- `curl http://localhost:8255/health` → `000` (unreachable)
- `reports/qa/goal-mcp-loop-iter-20-evidence/` → exists but is **completely empty** (no screenshots, no md5sums) — the phase spec's own NOTES section requires screenshot evidence with md5sum hygiene for exactly the three J-13 assertions; none exists.
- `runs/goal-mcp-loop-iter-20/status.json` → `"status": "complete"`, `"current_step": "audit_passed"`, but **`"browser_checks_run": false`**, and its own `next_action` field still reads: "...proceed with the normal reviewer re-review, then the canonical browser-qa-agent lane for J-13 (browser_checks_run still false)... plus the required-still-passing regression replay (J-01, J-03, J-05, J-10, J-12)." The pipeline's own machine-readable status has not been updated to reflect that this ever happened, because it did not.

This confirms the gap is current, not merely historical/already-resolved by a later step.

---

## Blocking Issues

1. **Browser QA was never executed; DoD line 1 is unmet by the named agent, and no documented reason establishes the SKIP as acceptable for this phase.**
   `reports/phase-goal-mcp-loop-iter-20-ui-test-results.md` records a blanket SKIP — 0/22 tests run, including all 14 P1 cases — because both services were unreachable at precondition check. `docs/phases/goal-mcp-loop-iter-20.md`'s DEFINITION OF DONE line 1 explicitly requires "Target journey J-13 passes via browser-qa-agent (all three steps: 548-pool Fetch scope; two-group split legend; hover distinguishes a bars-but-no-snapshot date from a snapshot date)" — this has not happened via the canonical lane. This is a `Frontend Present: yes` phase whose entire content is visual/UX (legend colors, tooltips, a removed dropdown option) — exactly the category of change browser verification exists for, not a backend-only phase where a SKIP would be defensible under this gate's documented exception. Both downstream gates that read this same evidence independently flagged it as open, not resolved: the audit (finding T3, "no screenshot evidence exists... DoD #1 is unmet by the named agent") and the ux-regression review (verdict `UX-REGRESSION-WARN`, "zero independent verification of J-13 happened before this review," recommendation #1 "Re-dispatch browser-qa-agent now"). The phase spec's own NOTES section pre-emptively warns against exactly this failure mode: "do not accept a status.json/QA 'ready to ship' over a '-fail-' frame in the evidence folder; reconcile self-reported blockers against the actual evidence dir and the ux-regression/closure verdicts" — the live re-check above confirms the evidence dir is in fact empty right now.
   **Remediation**:
   a. Avoid re-hitting the stale-bundle trap the ux-regression reviewer already found (`scripts/start-frontend.sh`'s staleness stamp only checks the backend URL, not frontend source freshness): run `rm -rf apps/frontend/.next` first.
   b. Bring up both services in prod mode — `scripts/start-backend.sh` then `scripts/start-frontend.sh` (never `dev.sh`) — and confirm reachability (`curl http://localhost:8255/health`, `curl http://localhost:3255`) before dispatching QA.
   c. Re-dispatch the browser-qa-agent against `reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md` in full: execute (not code-inspect) all 22 cases, with a real recorded PASS/FAIL on at minimum the 14 P1 cases (UT-01–05, UT-10–12, UT-14, UT-17–21).
   d. Capture the screenshot evidence the phase spec requires into `reports/qa/goal-mcp-loop-iter-20-evidence/` (full-page or element-clip captures, legend and both hovered cells scrolled into frame, `md5sum`'d per the hygiene NOTE).
   e. Update `runs/goal-mcp-loop-iter-20/status.json`'s `browser_checks_run` to `true` once genuinely executed.
   f. Re-submit to phase-closure-auditor.

2. **Three of five required-still-passing regression journeys have no live evidence from anyone this iteration.**
   The DoD requires "Required-still-passing journeys J-01, J-03, J-05, J-10, J-12 remain green (deterministic replay)." Only J-01 (live Sector-sort check) and incidentally J-03 (same spot-check) have any live evidence, both from the ux-regression reviewer's own supplementary check — not from browser-qa-agent. J-05 (`/evidence`), J-10 (deep-history chart), and J-12 (universe-count consistency) were assessed only by "the changed files don't overlap" reasoning (audit finding T5), never opened in a browser this iteration.
   **Remediation**: No new test design is needed — `ui-test-plan.md` already contains UT-19 (J-05), UT-20 (J-10), and UT-21 (J-12) for exactly this purpose. Fold their execution into the browser-qa-agent re-dispatch in Issue #1.

3. **The QA report's browser-verification claims are internally contradicted by another required pipeline artifact from the same run.**
   `reports/qa/goal-mcp-loop-iter-20-qa.md` states "Frontend is running and responsive" / "Frontend running at http://localhost:3255 as expected" from a curl check, then grades 12 of 16 functional test cases (TC-03 through TC-12, TC-16 — every one of them behavior that only a live browser can confirm) as PASS. `reports/phase-goal-mcp-loop-iter-20-ui-test-results.md` — from the same phase, same day, also via a curl precondition check — records the opposite: `000` (connection failure) on both `:3255` and `:8255`. Independent of which check is stale, the QA report's own methodology column for those 12 rows reads "Code verification" / "Code review," not browser execution, while `status.json` records `browser_checks_run: false` — i.e., the QA report grades browser-dependent test cases as PASS without ever having exercised a browser, which is the exact false-completion pattern this gate exists to catch. Independently corroborated by the audit (finding T4: "the QA report overstates its browser verification... the QA artifact itself remains misleading").
   **Remediation**: When browser-qa-agent is re-dispatched (Issue #1), have QA reconcile or re-issue the Browser Checks section and the TC-03–12/TC-16 rows of `reports/qa/goal-mcp-loop-iter-20-qa.md` to cite the real browser-qa-agent run rather than code review, so the two required artifacts no longer disagree about service reachability or verification method.

---

## Non-Blocking Notes

- `scripts/start-frontend.sh`'s staleness stamp (`.next/.qa-serve-base`) checks only the baked backend URL/port, never frontend-source freshness. It already silently served a stale, pre-iter-20 bundle once this iteration (caught only because the ux-regression reviewer happened to inspect the live DOM and noticed the Expand option was still present). Flagged by the audit as finding O1, a non-blocking tooling follow-up: hash/mtime the frontend source tree into the staleness stamp, or unconditionally `rm -rf .next` before any QA/audit browser pass. Remediation step 1a above works around it for this phase; the underlying script gap should still be filed as a follow-up so a future iteration doesn't grade a stale bundle undetected.
- The underlying code substance of J-13 is well-supported by independent, non-browser evidence and is not itself in doubt: 102/102 scoped backend tests pass (dev and QA both ran the suite to completion independently), `tsc --noEmit` is clean, the review report independently re-verified all three fix-notes findings, the audit found zero critical/important code defects, and the ux-regression reviewer's own live DOM/computed-style spot-check (performed after forcing a clean rebuild) confirmed every J-13 visual/behavioral DoD criterion matches spec exactly (exact option count, two-group legend, `#a6c8f2`/`#a78bfa` computed colors, exact tooltip text, honest static-caps copy). This CLOSURE-FAIL is about the missing and internally-contradicted evidence trail for the canonical browser-qa-agent lane and three unreplayed regression journeys — not a suspected defect in the shipped code.
