# Phase goal-ops-hardening-iter-6 — UX Regression Review

**Date:** 2026-07-21

**Verdict:** UX-REGRESSION-PASS

This iteration is a frontend-only request-timing fix (no new endpoint, no new displayed value, no new
button/form/nav entry) closing J-06's last two real-browser latency violations from iter-5. The classic
"hidden/undiscoverable capability" axis does not apply (nothing new was added) — confirmed by `git diff
HEAD -- apps/frontend/` touching exactly two files (`components/phase-cross-view-card.tsx`,
`app/data/page.tsx`), both fetch-timing-only changes, no new JSX/markup. The regression axis is
substantively clean: the one component-level risk this iteration's own `ui-surface-map.md` flagged (a
"new race window" in the abort/cleanup path) was explicitly live-tested (UT-04, TC-10) and holds, and both
required-still-passing journeys with a shared-code footprint (J-04, J-05) were freshly re-verified live
this cycle and PASS — a materially stronger regression-evidence position than iter-5, which shipped with
J-01 failing its replay and J-04/J-05 completely unreplayed (see `reports/phase-goal-ops-hardening-iter-5-ux-regression.md`,
verdict FAIL). Two non-blocking documentation/process items are flagged below for the evaluator's
attention — neither represents an actual product-UX defect.

---

## New Capability Discoverability

Per `reports/phase-goal-ops-hardening-iter-6-user-visible-changes.md` §"What Users Can Now Do" and the
plan's own "UI Evolution" section: **no new user-facing capability**. Confirmed independently via
`git diff HEAD -- apps/frontend/`: the only two changed files are `phase-cross-view-card.tsx` (wraps the
existing `Promise.all` fetch in a `window.setTimeout(..., 250)`) and `app/data/page.tsx` (wraps the
existing `loadAvailability()` call in a `window.setTimeout(..., 2500)`). No new component, route, button,
form field, or nav entry appears in either diff. Nothing to assess for click-depth or label clarity this
cycle — this axis is clean by construction.

---

## Regression Risk

### `phase-cross-view-card.tsx` — Dashboard (`/`), "Regime × phase cross-view" card

**Prior feature served:** the cross-view chart itself (home page, 0 clicks, part of J-05's registered
Dashboard row per `blueprint.md`) plus its Hide/Show persisted-toggle affordance.
**Current change:** the on-mount `Promise.all` fetch now fires inside a 250ms `setTimeout` instead of
immediately; the cleanup function now clears both the timer and the `AbortController` (previously just the
controller) — a genuinely new code path (a timer that can fire, or be cleared, independently of the fetch
it guards).
**Risk assessed:** Medium going in (new race window on rapid as-of toggling), **downgraded to Low
post-verification**: `ui-surface-map.md` correctly flagged this exact risk and prescribed the test; QA's
UT-04 (two rapid "◀" clicks within ~1s of load) and the dev handoff's own TC-10 account both confirm the
card never renders blank/frozen and correctly settles to the newly-selected date's data. UT-06 additionally
confirms the Hide/Show toggle (a J-0x-era affordance, unrelated to this diff but sharing the same
component) still re-mounts, re-fetches, and re-renders cleanly. UT-05 confirms sibling Dashboard cards
(Market Regime, Market Phase & Severity) are unaffected.

### `app/data/page.tsx` — Data Manager (`/data`), availability heatmap loader

**Prior feature served:** the coverage/availability heatmap (feeds `AvailabilityHeatmap`), the job-history
panel this same page hosts (target of J-01's golden script), and J-61's "click a heatmap day to prefill the
job form" affordance (same file, different effect — untouched).
**Current change:** `loadAvailability()` now fires 2500ms after `loadOverview()` on the page's *first*
mount effect only; every other call site (job completion, retry/dismiss, removal) still calls both
together, unchanged (confirmed via the diff — only the mount `useEffect` is touched).
**Risk assessed:** Low. The heatmap's own loading/error/empty render branches are untouched (only the
timing of the fetch that feeds them changed); UT-07/UT-08 confirm the spinner covers the full 2.5s deferral
window with no blank gap, and the grid renders correctly after. UT-10/UT-11 (weekend-backfill flow, form
validation) — both share this page and were unaffected. J-61's click-to-prefill behavior lives in a
separate, untouched effect and wasn't a plausible contention target.

### `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (test-infra target, not product code)

**Prior status:** iter-5's ux-regression review (FAIL verdict) flagged this exact script's step 6 as
broken — asserting a stale, now-buried `"2026-05-15"` text on `/scanner-runs`, unrelated to the script's
own submitted action.
**Current change:** step 6 rewritten to assert `"no new snapshots"` against `/data`'s own persisted
run-history entry for the exact backfill the script's own steps 2–4 submit.
**Verification:** live-verified by the developer (submitted the exact script through the running app,
confirmed both step-5 and the new step-6 text persist across a reload) and independently by the regression
replay (`reports/phase-goal-ops-hardening-iter-6-regression-replay-results.md`: `UT-J-01 PASS`,
"journey replayed end-to-end; all expects held") and by QA's own UT-10. This closes the exact gap iter-5's
review flagged as a FAIL trigger — genuinely resolved, not merely reworded.

### Pre-existing pattern surfaced (not caused) by this iteration's own error-path tests

QA's UT-03 and UT-09 (both P2, non-gating) found that neither `PhaseCrossViewCard`'s nor
`AvailabilityHeatmap`'s own independent "X unavailable" error text ever renders under a full-backend-outage
precondition, because each component is nested inside its parent page's own top-level `state.kind ===
"ok"` gate — when the top-level fetch fails, the whole below-the-fold body (including these two components)
never mounts, so a single page-level "Backend unavailable" card is shown instead of two nested ones.
**This is confirmed pre-existing, not introduced by this iteration**: `git diff HEAD -- apps/frontend/app/page.tsx`
is empty (zero changes) and the corresponding gating structure in `app/data/page.tsx` is confirmed
byte-unchanged (only the `AVAILABILITY_FETCH_STAGGER_MS` timer was added). Functionally the product never
goes blank and never fabricates data under backend-down conditions on either page (AG-8's substance holds)
— it just shows one honest page-level error instead of two nested independent ones, which is a legitimate,
pre-existing architectural choice that these two components' own "error" render branches are effectively
unreachable dead code under a full-outage precondition. Not a new regression; worth a backlog note (either
delete the now-unreachable branches, or restructure the gating so nested cards can show their own error
state) but does not affect this iteration's verdict.

### Other shared surfaces checked, no risk

- Navigation/sidebar/layout components: not in the diff.
- `blueprint.md`: updated with additive notes only (no row's producer/endpoint/module changed) — confirmed
  by reading the relevant rows directly; no `blueprint.reapproval-requested` entry, consistent with "no
  nav/route change."
- `IndexVendorPanel` / `MacroFeedPanel` (other on-mount fetchers on `/data`): not touched, per the plan's
  explicit scoping and confirmed by the diff.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Status |
|---|---|---|
| Fetch-timing change (Dashboard 250ms / Data Manager 2500ms defer) | Invisible by design — same skeleton/spinner covers the window; only speed improved | Correctly scoped as non-visible per `user-visible-changes.md`'s own framing |
| `GET /api/data/availability`'s first committed budget row | `reports/perf-budgets.md` only — explicitly an engineering artifact, not a UI surface (matches iter-5's precedent for this same file) | Correctly scoped, no gap |
| No new backend endpoint, module, or Data Contract value | N/A | Confirmed — `implementation-summary.md`'s "Backend-Only Items: None" and the dev handoff's "no backend Python file changed" both agree with `user-visible-changes.md`'s "Not Visible Yet: None" |

No unexposed backend capability found — this axis is clean by construction (there is no new backend
capability this iteration to check parity against).

**One artifact-consistency gap worth flagging (not a UI/backend parity gap in the classic sense, but
affects trust in the UX documentation):** `reports/phase-goal-ops-hardening-iter-6-user-visible-changes.md`
(written 00:55, before the dev's later fix pass) still describes `/evidence` and `/research` event-study
lab as carrying an unresolved, severe, still-present problem — "`/evidence` measured 555.97 seconds…
Anyone opening either page today should expect this multi-second-to-multi-minute wait." The dev handoff's
later "Fix Notes" section (added 02:01, after re-measuring on an idle host) retracted this: the 555.97s/
91.95s figures were a measurement-contamination artifact (concurrent 84-minute pytest run + a stale
diagnostic `curl` + the wrong budget class applied to a cold-cache path), and clean re-measurement shows
`/evidence` at ~22ms warm (bounded ~73s one-time cold miss, within its already-committed Item-I budget of
"warm ≤3s + bounded cold miss") and `/research/event-study` at 3–635ms. `reports/perf-budgets.md` and
`reports/phase-goal-ops-hardening-iter-6-implementation-summary.md` (both updated after the fix pass)
correctly carry the correction; `user-visible-changes.md` and `docs/handoffs/goal-ops-hardening-iter-6-frontend.md`
do not — both still describe the superseded, contaminated figures as current reality. Since
`user-visible-changes.md` is the canonical "what users see" artifact this review (and the evaluator) is
told to read, a reader relying on it alone would incorrectly conclude two pages are severely broken today.

---

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- None confirmed. The one new code path this iteration introduced (timer+abort dual-cleanup on
  `PhaseCrossViewCard`) was explicitly flagged as a regression risk by this iteration's own
  `ui-surface-map.md` and was live-verified safe (UT-04, TC-10). Both required-still-passing journeys that
  share touched files' surrounding page context (J-04, J-05) were freshly re-verified live this cycle and
  PASS — see `reports/phase-goal-ops-hardening-iter-6-ui-test-results.llm.md` rows UT-J-04/UT-J-05.
- **Pre-existing, not new:** `PhaseCrossViewCard`'s and `AvailabilityHeatmap`'s own independent error-state
  render branches are unreachable dead code under a full-backend-outage precondition (UT-03, UT-09, P2,
  non-gating) — confirmed via `git diff` that the gating structure responsible predates this iteration.
  Recommend a backlog note for whoever owns page-level error-boundary architecture, not an action for this
  iteration.

### Visual Consistency
- No new pages or components were added, so there is nothing new to check against DESIGN SYSTEM tokens.
  Both touched components reuse their exact pre-existing loading/error/empty render branches verbatim
  (confirmed by diff — only the `setTimeout` wrapper is new code; no JSX/className changed). QA's
  screenshots (UT-01, UT-02, UT-07, UT-08) show the same skeleton (`animate-pulse`) and spinner
  (`Loader2` + "Loading availability…") idioms as documented in prior iterations' visual baselines.

### Process / Artifact-Trust Notes (non-blocking, flagged for the evaluator)
- **Merged `reports/phase-goal-ops-hardening-iter-6-ui-test-results.md` reports "Browser QA Verdict: FAIL"
  / "14/18 journeys passed," while the raw `reports/phase-goal-ops-hardening-iter-6-ui-test-results.llm.md`
  (browser-qa-agent's own primary artifact) reports "Browser QA Verdict: PASS" / "12/14 test-plan cases
  PASS, 2/14 FAIL (both P2, non-gating)."** This is the exact "merge script drops `## Notes` and doesn't
  respect priority-based gating" pattern the phase spec's own NOTES section pre-warned about (citing the
  iter-3/iter-4 lesson): the merge script appears to count any FAIL row (including the two non-gating P2
  error-architecture cases above, and possibly the two INFORMATIONAL/P3 rows UT-13/UT-14) toward an
  overall FAIL, while the raw file's own explicit HTML-comment verdict rule ("All P1 tests… pass… Two P2
  error-state tests FAIL… but… does not gate the verdict per the P1/smoke/happy-path rule") computes PASS.
  This review's regression assessment above is based on the raw file plus underlying evidence (screenshots,
  live re-verification), which is internally consistent and does not show a functional regression — but
  flagging this discrepancy explicitly so the evaluator does not score this iteration against the merged
  file's misleading top-line FAIL without reading the raw file, per the phase spec's own stated caution.
- **`user-visible-changes.md`'s characterization of `/evidence`/`/research` is stale relative to the dev
  handoff's later "Fix Notes" correction** (see UI vs Backend Parity above). Recommend
  `ui-impact-analyst` (or whoever owns that artifact) issue a short addendum before this session's
  evaluator/auditor pass, so the canonical "what users see" document doesn't contradict the corrected
  `perf-budgets.md`/`implementation-summary.md`.

---

## Recommendation

No UI action required — discoverability, regression risk, and UI/backend parity are all clean this
iteration, with stronger regression evidence (fresh live J-04/J-05 verification, a resolved J-01 script)
than iter-5 shipped with. Two non-blocking documentation-hygiene items should be corrected before the
session's evaluator/auditor treats this iteration as fully closed, so neither misleads a downstream reader:
1. Add a short addendum (or re-issue) `reports/phase-goal-ops-hardening-iter-6-user-visible-changes.md`
   to reflect the dev handoff's "Fix Notes" correction on `/evidence`/`/research` — currently it still
   describes a severe, unresolved problem that the dev's own later re-measurement retracted.
2. When scoring this iteration, use `reports/phase-goal-ops-hardening-iter-6-ui-test-results.llm.md`
   (raw, PASS) as ground truth over the merged `ui-test-results.md` (FAIL) — the merge script's
   priority-blind FAIL rollup is a known, previously-documented artifact-fidelity bug, not a fresh signal.
