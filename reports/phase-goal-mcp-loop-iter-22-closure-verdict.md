# Phase goal-mcp-loop-iter-22 — Closure Verdict

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Summary

The standard pipeline gates (review, QA, audit) each currently show a PASS-class verdict. However,
this phase went through an audit-FAIL → dev-fix → re-review/re-QA/re-audit cycle, and two of the
UI-evidence artifacts this gate is specifically chartered to check — the canonical
**browser-qa-agent** report (`ui-test-results.md`) and the **ux-regression-reviewer** report
(`ux-regression.md`) — were **never re-run after the fix**. Both remain frozen at their pre-fix
state and both currently record a FAIL-class verdict for the exact literal DoD acceptance
criterion of this iteration's target journey (J-14, DoD item (a)). The phase spec's own Definition
of Done requires the target journey to "pass **via browser-qa-agent**" — a specific, named-agent
requirement that has not been satisfied on the current, fixed code. A different agent's internal
spot-check (the "qa" agent, not "browser-qa-agent") and the auditor's own independent re-verification
are good corroborating signals the fix works, but they do not substitute for the specific artifact
the DoD names, and the audit's own finding (T3) explicitly says this reconciliation is still owed
to "a downstream gate" — which is this gate.

This is not a rejection of the underlying work — the F1 fix (`minBarSpacing: 0.02`) is well-reasoned,
independently corroborated by the auditor's pixel-level screenshot comparison, and by the QA agent's
own fresh TC-01 screenshot. The blocking issue is evidentiary/process hygiene: the required,
DoD-named verification artifact must be regenerated against the current code before this phase can
truthfully be called closed, rather than left standing as an unreconciled contradiction in the
artifact record.

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-22-review.md`) | exists | PASS |
| QA report (`reports/qa/goal-mcp-loop-iter-22-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-22-audit.md`) | exists | PASS_WITH_GAPS |

Step 1 (standard pipeline gates) passes at face value. The blocking issue identified below comes
from the deeper UI-evidence cross-check this gate exists to perform (Steps 2–4), not from a missing
or failing standard gate.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes (84 lines) | yes — specific, detailed | OK |
| user-visible-changes.md | yes | yes (38 lines) | yes — specific | OK, but see Blocking Issue #3 (a core claim was falsified by later-produced evidence and never reconciled) |
| ui-surface-map.md | yes | yes (63 lines) | yes — names exact routes/components/files | OK |
| ui-test-plan.md | yes | yes (625 lines) | yes — 19 numbered test cases with exact steps | OK |
| ui-test-results.md | yes | yes (203 lines) | yes — detailed, real execution evidence, not placeholder | **Content is stale: overall Verdict is FAIL, dated 16:21, never re-run after the 17:11 dev fix pass. See Blocking Issue #1.** |
| what-to-click.md | yes | yes (89 lines) | yes — 7 numbered steps with exact expected outcomes | OK |

Additional artifact reviewed per this gate's task (not one of the core 6, but explicitly in scope):

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| ux-regression.md | yes | yes (82 lines) | yes — specific, cites exact evidence files | **Content is stale: overall Verdict is UX-REGRESSION-FAIL, dated 16:39, its own Recommendation #1 says "Blocking," never re-run after the 17:11 dev fix pass. See Blocking Issue #2.** |

All 6 required files plus the UX regression report exist and contain substantive, non-placeholder
content — there is no missing-artifact or vagueness problem here. The problem is that two of them
record a verdict that contradicts the phase's current claimed state and has not been superseded by
a fresh run of the same agent.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes, several (deep benchmark lines, vendor
      labels, new `/data` panel, VIX/macro-proxy lines).
- [x] ui-surface-map has specific route/component entries — yes (`/`, `/data`,
      `phase-cross-view-chart.tsx`, `index-vendor-panel.tsx`, exact line numbers).
- [x] ui-test-plan has specific steps with exact actions and expected results — yes, exceptionally
      detailed (19 cases, byte-exact expected legend text, exact colors, exact dates).
- [ ] ui-test-results shows execution evidence **consistent with the phase's current claimed
      state** — execution evidence exists and is real, but the recorded verdict (FAIL) is stale
      relative to a code fix applied ~50 minutes after this report was written, and has not been
      reconciled. The 2 SKIPPED cases (UT-11, UT-12) are P3/tooling-limited and correctly
      documented — those are not the problem.
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 7 steps.
- [ ] implementation-summary claims are consistent with ui-test-results evidence — **NO.**
      `implementation-summary.md` (updated at 17:12, post-fix) asserts: "The chart now opens showing
      the full history by default (audit fix)... This was verified live in a browser: with no
      interaction, the left edge of the chart reads March 1996..." `ui-test-results.md` (16:21,
      pre-fix, unmodified since) documents the literal opposite as a reproducible P1 FAIL (tested 3×
      at 1440×900, plus 1920×1080 and 3840×1200; default view never reaches earlier than ~2015). The
      artifact record currently contains a direct, unresolved contradiction on the phase's single
      most important acceptance criterion.

---

## Blocking Issues

1. **Canonical browser-qa-agent verdict (`ui-test-results.md`) is a stale, unreconciled FAIL for
   the literal DoD target-journey acceptance criterion.**
   `reports/phase-goal-mcp-loop-iter-22-ui-test-results.md` (mtime 2026-07-08 16:21) records
   **Verdict: FAIL**, driven by UT-03 (P1, happy-path) — the Dashboard "Regime × phase cross-view"
   chart's default (and maximum-zoomed-out) view never shows the deep 1996 history at any common
   viewport, directly contradicting DoD item (a): "the Dashboard major-indexes chart rendering a
   deep benchmark line (^SPX) that extends before SPY's 2005 start." The phase spec's own DoD
   requires this journey to "pass **via browser-qa-agent**" — a specific named-agent requirement.
   The dev's subsequent "Fix Notes" section (appended to the dev handoff at 17:11, ~50 minutes after
   this report was written) applied `minBarSpacing: 0.02` to fix exactly this defect. After that fix,
   only the reviewer (17:23, source-level), the "qa" agent (17:34, its own internal TC-01 retest with
   fresh screenshots — a different agent than "browser-qa-agent"), and the auditor (17:47,
   independent code/screenshot re-verification) ran again. **The browser-qa-agent itself was never
   re-invoked.** The audit's own finding T3 explicitly names this gap: "the canonical browser-QA
   report-of-record still reads FAIL... should be reconciled so a downstream gate does not read the
   stale FAIL" — this gate is that downstream reader, and per this gate's charter a different agent's
   substitute spot-check cannot stand in for the DoD-named artifact.
   **Remediation:** Re-invoke the browser-qa-agent against the current (post-fix) build — services
   restarted per the harness-discipline lesson (`rm -rf apps/frontend/.next` first) — to regenerate
   `reports/phase-goal-mcp-loop-iter-22-ui-test-results.md` end-to-end (all 19 cases in
   `ui-test-plan.md`, not just UT-03), producing a fresh, current-dated, md5-distinct evidence set.
   Confirm the regenerated verdict is PASS before returning to this gate.

2. **UX regression verdict (`ux-regression.md`) is a stale, unreconciled UX-REGRESSION-FAIL that
   explicitly labels the same defect "Blocking."**
   `reports/phase-goal-mcp-loop-iter-22-ux-regression.md` (mtime 16:39, also pre-fix, sourced
   directly from the pre-fix `ui-test-results.md` evidence) records **Verdict: UX-REGRESSION-FAIL**.
   Its own Recommendation #1 reads: "**Blocking:** fix the Dashboard chart's default/reachable view
   so the committed 1996 history is actually visible without undocumented drag gestures before this
   iteration is treated as having delivered J-14." This report has not been re-run since the dev's
   fix pass, so its own stated blocking condition has never been lifted by its own re-verification.
   It also separately flags that `user-visible-changes.md`'s claim ("renders automatically... no
   click required") was disproven and "should not be read as an accurate record... until corrected"
   — see Issue #3.
   **Remediation:** Re-invoke the ux-regression-reviewer against the current build, after Issue #1's
   browser-qa-agent re-run produces fresh evidence for it to read. Confirm its Hidden-Capabilities /
   Discoverability table and Recommendation section no longer flag the fixed behavior as blocking.

3. **`user-visible-changes.md`'s core capability claim was falsified by the artifact record and has
   only been "corrected" by the developer's own self-assessment, not by independent re-verification.**
   `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md` (mtime 15:02, pre-fix, written by
   ui-impact-analyst) states the deep benchmark lines render "automatically on page load... no new
   click or control is required." `ui-test-results.md`'s UT-03 (produced later that same run)
   reproducibly disproved this exact claim on the code as it stood at the time, and
   ux-regression.md flagged the document as unreliable until corrected. The dev's own Fix Notes
   assert the claim is "now TRUE" post-fix ("T3... no correction is owed") — but this is the
   implementing developer's self-assessment of their own claim, which is precisely the kind of
   self-verification the review/QA/UX-regression/audit separation of roles exists to avoid relying
   on alone.
   **Remediation:** Once Issue #1's browser-qa-agent re-run confirms PASS with fresh evidence, either
   regenerate `user-visible-changes.md` (ui-impact-analyst) against the current state or add an
   explicit reconciliation note citing the new evidence, so the claim rests on independent
   verification rather than the developer's own say-so.

These three issues share one root cause and one remediation path: re-run the browser-qa-agent and
ux-regression-reviewer against the current, already-fixed code, then let the resulting fresh
evidence settle `user-visible-changes.md`. Given how much independent corroborating evidence already
exists that the underlying fix works (QA's TC-01 screenshot, the auditor's pixel-level comparison of
`UT-03-fail-fullpage.png` vs `TC-01-chart-area.png`, the dev's live hover-to-1996-03-25 check), this
is expected to be a fast confirmatory re-run rather than a rediscovery of a real defect — but it must
actually happen and produce a current PASS from the named agents before this phase closes.

---

## Non-Blocking Notes

- **J-13 coverage gap (audit B5 / ux-regression "Coverage gap"):** loading the 3 deep symbols
  honestly shifted the `/data` availability-heatmap denominator 587→590; J-13 (required-still-passing)
  was not given a dedicated live replay with the same rigor as its six peer regression journeys.
  `availability-heatmap.tsx` is unmodified (`git diff` empty), so code risk is low. Recommended for
  the next iteration's regression pass, not blocking this one.
- **`^TNX` first-bar disclosure understates its DB history (audit F4):** the `/data` panel's
  disclosed "First bar" for `^TNX` (2021-01-04, byte-matching `meta.json` per the DoD's explicit
  instruction) is ~16 years later than the chart line's actual visible extent (DB has bars from
  2005-02-28). This is spec-compliant, conservative (understates rather than overstates), confined
  to one honestly-labeled proxy line, and already documented in the dev handoff's Known Issues. No
  in-scope fix exists (re-fetching/trimming `^TNX` is forbidden by goal.md §H).
  Same for `test_api_indexes.py`
  not finishing in-window — byte-identity is independently covered at the unit level and via a live
  `curl` check; confirm it's green when it finishes.
- **Orphaned dead code (`index-regime-chart.tsx` / `major-indexes-card.tsx`):** pre-existing (not
  introduced this iteration — an earlier iteration already replaced it with
  `phase-cross-view-chart.tsx`), transparently disclosed in every relevant artifact
  (dev handoff, ui-surface-map, user-visible-changes, review NOTE). A cleanup candidate for a future
  iteration, not a closure blocker.
- **Minor tooltip crowding (QA UT-05):** the longest vendor label ("^TNX · FRED-macro proxy")
  visually crowds its percentage value in the tooltip at default width — content is correct and
  legible via DOM extraction, just tightly spaced. Cosmetic only.
