# Iteration 33 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Summary

This iteration's spec-scoped work — genuinely fixing `scripts/start-frontend.sh` to build-if-stale then
`exec next start` (never `next dev`), the `measure-perf.sh` header correction, the `merge_ui_test_results.py`
`_ROW_RE` widen, and the resulting first-ever prod-mode J-06 11-page real-browser sweep appended to
`reports/perf-budgets.md` — touches no page/component source and introduces no new page, route, or Data
Contract value. Confirmed against the blueprint's IA table (J-06's canonical home is explicitly
`reports/perf-budgets.md`, "not a UI page") and Data Contract (this row's "N/A — a measurement artifact"
entry): the sweep only re-times already-registered rows (Regime score / market phase / forward-returns,
Index series, Coverage payload, Job history, Membership-timeline/research-hot-key) through their existing
producers/endpoints, appended to the same one file — no second artifact created.

A QA-FAIL retry round then landed real product UI, outside the original spec's "UI surface changes: None"
claim: browser QA found a genuine P1 defect (UT-11) — `/research/regime-lab`'s cold-cache path (60-90s,
one observed raw "Internal Server Error") left an unlabelled, indefinite skeleton with no feedback and no
retry. The fix adds a new pure module `apps/frontend/lib/lab-load-panel.ts` (`resolveLabLoadPanel`,
`formatElapsedSeconds`) and, in `apps/frontend/app/research/_labs.tsx`, a new `SlowComputeNotice` card, a
new `useElapsedSeconds` hook, and an optional `onRetry` prop on the existing shared `ResearchError` card,
wired only into `RegimeLabPage`. This is a legitimate, disclosed fix-mode response to a real QA finding
(not undeclared scope creep) — it is presentation-only: it reads, recomputes, and fabricates no figure: the
underlying fetch is still the same `GET /api/research/regime-lab?view=pooled` call, served by the same
`regime_lab_cached` producer, unchanged. I independently verified this by reading `lab-load-panel.ts`,
the `_labs.tsx` diff, and the dev/frontend handoffs' Fix Notes sections, and cross-checked against the
review report and the ux-regression-reviewer's report, which reached the same characterization.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score / market phase / forward-returns (existing row) | OK — re-timed only, same producers/endpoints | `reports/perf-budgets.md` "## Iteration 33" section (diff vs `197fe13f`) |
| Index series | OK — re-timed only (`GET /api/indexes?full=true`), same `IndexSeriesCache`/`compute_index_series` | `reports/perf-budgets.md` "## Iteration 33" |
| Coverage payload | OK — re-timed only (`GET /api/data`), same producer | `reports/perf-budgets.md` "## Iteration 33" |
| Job history / Backfill run-summary | OK — untouched this iteration (no backend file changed) | dev handoff "Files Changed" — no `apps/backend/app/**` entries |
| Membership-timeline / research hot-key caches (incl. `regime_lab_cached`) | OK — the UT-11 fix wraps this SAME cached read's pre-data UI state; no new endpoint, no client-side recomputation of the served figures | `apps/frontend/lib/lab-load-panel.ts:1-19` (docstring: "reads, recomputes, and fabricates NO figure"); `apps/frontend/app/research/_labs.tsx` `RegimeLabPage` still calls the one existing fetch |
| Page performance budgets | OK — appended to the SAME `reports/perf-budgets.md`, no second file | `git diff 197fe13f -- reports/perf-budgets.md` (172 insertions, 0 deletions, single file) |
| "Elapsed seconds" / "still computing" notice (new, iter-33) | UNREGISTERED-BUT-NOT-A-CONTRACT-VALUE | `apps/frontend/lib/lab-load-panel.ts:34-38` — a client-side loading-state timer, not a served/displayed business value; matches the blueprint's own iter-18/23 precedent ("a log line is not a served/displayed value") |

No duplicate computation and no non-canonical source found for any registered value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/regime-lab` (UT-11 fix: `SlowComputeNotice`, Retry) | OK — no new page/route, reachability unchanged (Research → Regime Lab, 2 clicks) | Blueprint IA table row "Research /research — index of 15 labs"; frontend handoff confirms unchanged reachability; no `sidebar.tsx`/router change in the diff |
| J-06 measurement (launcher fix + sweep) | OK — canonical home is `reports/perf-budgets.md`, not a UI page, per blueprint | Blueprint "Feature / journey homes" table, J-06 row |

No new page, route, or nav entry. No parallel shell. No duplicate home.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Sibling-lab inconsistency (the reason for WARN, not PASS).** `resolveLabLoadPanel`/`SlowComputeNotice`/
  Retry were wired into `RegimeLabPage` only. `/research/phase-severity-lab`, `/research/regime-phase-factor`,
  `/research/factor-lab`, and `apps/frontend/app/research/severity-velocity/page.tsx` still render a bare,
  unlabelled `LabSkeleton` on a slow load and their `ResearchError` call sites still pass no `onRetry` — the
  identical UX failure shape UT-11 just proved is a real P1 on Regime Lab remains structurally present on
  every sibling Research lab, one measurement away from recurring if any of their computations grow slow on
  a deeper history basis. Both the dev handoff and the ux-regression-reviewer's report disclose this
  honestly and call it non-blocking/deliberately deferred (per fix-mode discipline: fix only the QA blocker,
  not every lookalike surface). `resolveLabLoadPanel` is already generic and exported for reuse — recommend
  the next iteration that touches a research lab, or a dedicated small iteration, wires the same resolver
  into the remaining lab pages so "still computing"/Retry behavior is consistent across the whole Research
  section rather than present on only one of five+ lab routes.
- **Pipeline-artifact staleness (procedural, not a product defect — already flagged by the
  ux-regression-reviewer independently).** `reports/phase-goal-ops-hardening-iter-33-ui-surface-map.md` and
  `reports/phase-goal-ops-hardening-iter-33-user-visible-changes.md` (both timestamped ~11:08, i.e. before
  the QA-FAIL fix-mode round) state "No `apps/frontend/app|components|lib/**/*.tsx` file changed" —
  contradicted by the actual final diff (`_labs.tsx` changed, `lib/lab-load-panel.ts`/`.test.ts` added at
  ~13:10-13:12). I read the diff and the dev/frontend handoffs directly rather than relying on these two
  reports, so this audit's conclusions are unaffected, but the artifact trail itself is misleading to a
  future reader who trusts only the "official" UI-impact docs. Recommend regenerating
  `ui-surface-map.md`/`user-visible-changes.md` (and the demo script/results, also pre-fix) after any
  fix-mode round that lands real UI changes, matching the recommendation already on record in
  `reports/reviews/goal-ops-hardening-iter-33-review.md`.
- No labeling/formatting drift found for any Data Contract value across pages this iteration.
