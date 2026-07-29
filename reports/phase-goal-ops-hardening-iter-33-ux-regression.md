# Phase goal-ops-hardening-iter-33 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-WARN

---

## Scope note

This iteration's spec-scoped work (`scripts/start-frontend.sh` dev→prod fix, `merge_ui_test_results.py`
regex widen, the J-06 real-browser sweep) is explicitly **not** a new user-facing capability — plan's own
UI Evolution section says so, and the first-pass dev/ui-impact-analyst artifacts agree. But QA's first
pass (`reports/qa/goal-ops-hardening-iter-33-qa.md`, superseded verdict FAIL) found a genuine P1 UX defect
on `/research/regime-lab` (indefinite unlabelled skeleton on a 60–90s cold compute, one observed raw
"Internal Server Error"), and the fix-mode retry shipped **real product UI** in response: a new
`apps/frontend/lib/lab-load-panel.ts` resolver and a modified `apps/frontend/app/research/_labs.tsx`
(new `SlowComputeNotice`/`useElapsedSeconds`, an optional `onRetry` on the shared `ResearchError` card).
This review covers both the spec-scoped launcher fix (no UI surface) and this in-flight UI fix (real UI
surface, verified below).

## New Capability Discoverability

- **"Still computing — Ns elapsed" notice** (`SlowComputeNotice`, `_labs.tsx:211`): appears automatically,
  in place, on the already-reachable `/research/regime-lab` route once a fetch has been pending >3s
  (`SLOW_COMPUTE_NOTICE_AFTER_SECONDS`). No navigation change, no new nav entry — it needs none, since it
  replaces an existing indefinite-skeleton state on a page UT-15 already confirmed is 2 clicks from the
  Dashboard (Research → Regime Lab). Discoverability is inherent, not a gap.
- **Retry button on the "Backend unavailable" card** (`ResearchError`, `_labs.tsx:179`): appears only on a
  fetch failure, in place, on the same page. Same reasoning — no separate discovery path needed, the
  control surfaces exactly when it's relevant (a failed load), which is the correct place for it.
- Both are backed by real code, confirmed by direct read of `apps/frontend/lib/lab-load-panel.ts` and
  `apps/frontend/app/research/_labs.tsx:4210-4282` (`RegimeLabPage` wires `resolveLabLoadPanel(...)` and
  passes `onRetry={() => setAttempt((p) => p + 1)}`), not just asserted in a handoff.
- No discoverability gap for either control.

## Regression Risk

`ResearchError` is a **shared component** used by four call sites: `RegimeLabPage` (this iteration, now
with `onRetry`), `FactorLabPage` (`_labs.tsx:312`, `what="The Factor-Lab evidence"`, no `onRetry`),
`MarketPhaseSeverityLabPage` (`_labs.tsx:4561`, no `onRetry`), and
`apps/frontend/app/research/severity-velocity/page.tsx:92` (no `onRetry`). Verified by direct grep + read:
`onRetry` is optional (`onRetry?: () => void`) and the Retry `<button>` is only rendered when it's passed
(`{onRetry ? (...) : null}`), so the three untouched call sites render byte-identically to before. **Risk:
low, confirmed non-breaking.**

`WarmingState` (a visually similar sibling card used by the same labs for the readiness-warmup gate) was
not touched — `SlowComputeNotice` is a new, separate component that intentionally mirrors its styling
(same `border-warn bg-surface`/`Loader2` treatment), confirmed by reading both components side by side.

Golden-journey regression check: dev's pre-handoff dry run (8/8 PASS across J-01/J-03/J-04/J-05/J-06/J-07/
J-08/J-09) and the demo_runner.py regression replay results
(`reports/phase-goal-ops-hardening-iter-33-regression-replay-results.md`, 6/6 PASS on the required-still-
passing set J-01/J-03/J-04/J-05/J-08/J-09) both confirm no assertion regressed. Prior iteration (iter-32,
`docs/handoffs/goal-ops-hardening-iter-32-dev.md`) was backend-only (`forward_testing.py` accumulator
rewrite, no frontend file touched), so there is no iter-32 UI feature at risk here.

**Sibling-lab consistency gap (non-blocking, flagged for a future iteration):** `/research/phase-severity-
lab`, `/research/regime-phase-factor`, `/research/factor-lab`, and `/research/severity-velocity` still
render a bare, unlabelled `LabSkeleton` while loading, and their `ResearchError` call sites still have no
Retry — i.e., the exact defect shape UT-11 just proved is a real P1 (an indefinite silent load with no
"still working" signal) still exists, structurally unchanged, on every sibling research page. The
developer's own handoff discloses this honestly ("Their reads are materially faster today... none was in
QA's blocker list... deliberately left alone") — but that speed claim is asserted, not measured this
iteration (only `/research/regime-lab` was in this iteration's 11-page J-06 scope). If any sibling lab's
compute time grows on a future deep-history basis, it would reproduce the identical UX failure this
iteration just fixed on one page, with no automatic protection. `resolveLabLoadPanel` is generic and
already exported for reuse — the remaining work is wiring, not design.

## UI vs Backend Parity

- Launcher fix (`start-frontend.sh`): zero user-facing capability change (correctly, per plan) beyond
  removing the dev-mode overlay pill — verified TC-7 (zero console errors, no overlay, all 11 pages) via
  `reports/qa/goal-ops-hardening-iter-33-qa.md`.
- J-06 measurement: `reports/perf-budgets.md`'s new "Iteration 33" section is genuinely populated (real
  browser TTI + on-load latencies, all 11 pages, boot-to-health 0.093s) — not a placeholder. The one
  CRITICAL WARN (`/research/regime-lab` cold-cache 60–90s) is disclosed in full with root cause, not
  omitted — matches this file's own honest-WARN convention (TC-5).
- The UT-11 fix itself: backend compute path is explicitly unchanged (spec's "Backend: None" scope
  respected) — the parity gap this fix closes is purely about *honest status representation* on the
  frontend, not a new backend capability that needs surfacing. Nothing backend-only is left unexposed.

## Flags

### Hidden Capabilities
- None. Both new controls (computing notice, Retry) are visible in place on the same already-reachable
  page, with no separate discovery step required.

### Undiscoverable Capabilities
- None found.

### Potential Regressions
- None confirmed. `ResearchError`'s three other call sites (Factor Lab, Market-Phase-Severity Lab,
  Severity-velocity study) render unchanged — verified by reading each call site directly, not inferred
  from the handoff's claim alone.
- **Watch item, not a regression:** the sibling research labs share the identical unlabelled-skeleton /
  non-retryable-error shape UT-11 just proved defective on Regime Lab (see Regression Risk above). Not
  flagged as FAIL because it's a carried, pre-existing, honestly-disclosed limitation this iteration's
  scope explicitly did not touch — but it is the same failure mode, one measurement away from recurring.

### Visual Consistency
- `SlowComputeNotice` reuses the exact same design tokens and layout as the existing `WarmingState` card
  (`border-warn bg-surface p-5 text-sm`, `Loader2` spinner, `text-warn` heading) — confirmed by direct
  side-by-side read of both components. Consistent with the established visual style, no arbitrary values.
- The Retry `<button>` reuses the same class string already used by `app/error.tsx`'s retry affordance
  (per the frontend handoff's own claim) — token-based (`border-border`, `bg-surface-2`, `text-text`,
  `focus-visible:ring-accent`), no ad hoc hex/pixel values observed in the component source.
- No new page or layout was introduced, so there is no new page to check against the DESIGN SYSTEM beyond
  this one component pair, which passes.

### Pipeline-artifact staleness (procedural, not a product defect)
- The canonical UI-impact artifacts this review is pointed at
  (`reports/phase-goal-ops-hardening-iter-33-user-visible-changes.md`,
  `reports/phase-goal-ops-hardening-iter-33-ui-surface-map.md`, both timestamped 11:08) and the merged
  browser-QA report at the path named in this task
  (`reports/phase-goal-ops-hardening-iter-33-ui-test-results.md`, timestamped 12:35, header **"Browser QA
  Verdict: FAIL"**, UT-11 listed FAIL) all predate the fix-mode pass (dev/frontend handoffs updated
  13:10–13:12; QA's re-validation at `reports/qa/goal-ops-hardening-iter-33-qa.md`, timestamped 13:29,
  verdict **PASS**, UT-11 verified fixed). No later revision of `ui-test-results.md`,
  `user-visible-changes.md`, or `ui-surface-map.md` exists on disk (confirmed via `find -newer`) — so a
  reader who opens only those three "official" artifacts (as this review's own task instructions point to)
  would see a stale FAIL/"no UI change" picture that contradicts the actual, later, authoritative QA
  verdict and the real shipped code (`apps/frontend/lib/lab-load-panel.ts`,
  `apps/frontend/app/research/_labs.tsx`'s new components). This review resolved the contradiction by
  reading the dev/frontend handoffs and the current source files directly, and by trusting the
  chronologically-later `qa.md` PASS as authoritative. Recommend the pipeline regenerate
  `ui-test-results.md`/`user-visible-changes.md`/`ui-surface-map.md` (and the demo script/results, also
  pre-fix at 12:37) after any fix-mode round that lands real UI changes, so the "official" artifact trail
  matches the final shipped state instead of only the QA report doing so.

## Recommendation

1. No blocking action required — the shipped UT-11 fix is discoverable, non-regressive to the three other
   `ResearchError` call sites, and visually consistent with the existing `WarmingState` pattern.
2. Non-blocking, for iteration 34 or later: apply `resolveLabLoadPanel`/`SlowComputeNotice`/Retry to the
   sibling research labs (`/research/phase-severity-lab`, `/research/regime-phase-factor`,
   `/research/factor-lab`, `/research/severity-velocity`) before any of their computations grow slow enough
   to reproduce UT-11's exact failure mode — the resolver is already generic and exported for this reuse.
3. Non-blocking, framework hygiene: after a QA FAIL → fix-mode → QA PASS cycle that changes real UI code,
   regenerate the UI-impact/demo artifacts (`user-visible-changes.md`, `ui-surface-map.md`,
   `ui-test-results.md`, demo script/results) so they reflect the final state, not just the first pass —
   this iteration's own artifact trail is the concrete example of the gap.
