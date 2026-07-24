# Phase goal-ops-hardening-iter-20 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**No new capability was introduced this iteration** — confirmed identically across `docs/phases/goal-ops-hardening-iter-20.md` ("New user-facing capability: None new"), `runs/goal-ops-hardening-iter-20/plan.md` ("UI Evolution: New user-facing capability: none new"), `reports/phase-goal-ops-hardening-iter-20-implementation-summary.md` ("Backend-Only Items: None"), and the frontend dev handoff (`docs/handoffs/goal-ops-hardening-iter-20-frontend.md`: "No new component, fetch, field, or nav change"). This iteration is a latency fix (move a synchronous compute off the request thread) plus a copy correction on an **existing** capability: historical `/backtest` as-of viewing, live since iter-14/16/17.

Since there is no new capability, the relevant discoverability question is whether the corrected behavior is visible where a user would naturally encounter it — verified as follows:

| Existing capability | Navigation path | Clicks from home | Verified |
|---|---|---|---|
| `/backtest` page itself | Sidebar → "Backtest" (unchanged link, `apps/frontend/components/sidebar.tsx` — untouched this iteration, confirmed via `git log`/`git status`) | 1 | Live screenshot `UT-11-sidebar-nav.png`; sidebar list confirmed: Dashboard, Stocks, Themes, Sectors, Scanner Runs, **Backtest**, Research, Evidence, Watchlist, Methodology, Data Manager |
| Historical as-of selection | `asof-trigger` control (top-right on `/backtest`, pre-existing) → calendar picker | 2 (1 to page + 1 to open picker) | Live screenshots `UT-02-calendar-open.png`, `UT-02-historical-empty-state.png` |
| The corrected `RefreshingEvidenceBanner` / `EmptyState` copy | No navigation needed — renders automatically, in place, the moment a historical as-of is selected whose evidence isn't `"ready"` | 0 additional (same view) | Live screenshots `UT-05-refreshing-banner.png`, `UT-02-historical-empty-state.png` — I opened both images directly and visually confirmed the exact corrected sentences render on-screen (see below) |

I opened `UT-05-refreshing-banner.png` and `UT-02-historical-empty-state.png` directly (not just trusting the written QA report) and can independently confirm the rendered text matches what every report claims, verbatim:
- Banner (historical, `2005-07-15`): *"This date's own evidence is being computed in the background (started by viewing this page) and is not complete yet. The forward-tested evidence below is the last complete version — evidence as of 2005-07-01, generated 2026-07-24 17:32:54 ... Reload this page shortly to pick up this date's own evidence once the background compute finishes."*
- Empty state (historical, `2005-07-01`): *"Backtest evidence not yet computed / No forward-tested evidence exists yet for this date. Viewing this page has started computing it in the background — reload shortly to see it. No numbers are fabricated in the meantime."*

Both screenshots also show the "Backtest" sidebar item, the readiness badge ("Ready"), and the as-of trigger correctly labeled "(historical)" — the existing 1-click navigation path is intact and the corrected copy needs zero extra clicks to see once a historical date is selected. No hidden or undiscoverable capability.

---

## Regression Risk

Frontend diff this iteration is confined to **one file**: `apps/frontend/app/backtest/page.tsx` (confirmed via `git status`/`git diff` — no other frontend file appears in the changed-file list). Within that file, only two elements changed, both already owned by this exact feature's own prior iterations (not a different feature's shared component):

| Component | Prior feature it serves | Current change | Risk |
|---|---|---|---|
| `RefreshingEvidenceBanner` (`app/backtest/page.tsx`) | iter-16 (introduced), iter-17 (added `evidenceAsof` prop + `asofDate` fix) — J-08 evidence-status disclosure | iter-20 adds `isLatest: boolean` prop, branches 2 sentences | Low — same component's own lineage; verified live (screenshot) that the LATEST-view branch is unchanged and the historical branch renders correctly |
| `not_yet_computed` `EmptyState` description (`app/backtest/page.tsx`) | iter-16 (introduced), iter-17 (reworded) | iter-20 branches description on `is_latest` | Low — same reasoning; verified live |
| Rest of `/backtest` page (Survivorship banner, As-of scan summary, Scorecard, Return attribution, Leadership cohorts) | Multiple prior iterations | Untouched — confirmed both by the diff (no other JSX block edited) and live: UT-08 screenshots show every section fully populated during a historical first-view, only the bottom evidence footer shows the interim state | None |
| `Sidebar` / navigation | All features, every page | Untouched (`git log --oneline -- apps/frontend/components/sidebar.tsx` shows no ops-hardening commits touching it; `git status` shows it absent from this iteration's changed files) | None |
| `HealthBadge` / `useReadiness()` | iter-4 (added `awaiting_snapshot` state) | Explicitly NOT wired to by `RefreshingEvidenceBanner` (both the iter-16 and iter-20 code comments state this deliberately) — untouched this iteration | None — empirically confirmed too: UT-07 shows the readiness badge stayed "Ready" across ~15+ checks including during both cold-dispatch windows; `reports/perf-budgets.md` "Iteration 20" records 16/16 health samples `ready`, zero failures |
| `/data` Job progress panel / Run history (iter-1, iter-2) | Backfill range/zero-work/breakdown UX | Untouched this iteration (absent from changed-file list) | None — directly regression-tested: J-01/J-03/J-05 deterministic golden replay all **PASS** (`reports/phase-goal-ops-hardening-iter-20-regression-replay-results.md`, `UT-J-01/03/05` in the merged UI test results) |
| Dashboard `PhaseCrossViewCard` fetch-scheduling (iter-6) | J-06 dashboard latency fix | Untouched this iteration | None |

**The one genuinely new mechanism** — a background-thread, single-flight dispatch guard in `apps/backend/app/engine/forward_testing.py` — is a backend concurrency primitive on the exact subsystem cluster that had iter-13's REGRESSION history (per the phase spec's own risk framing). This is a backend change, not a UI component, so it is out of this review's direct remit, but its **user-visible** effect (does `/backtest` still work correctly under concurrency) is what I checked: live browser evidence (UT-01 through UT-11) all PASS, plus the developer's documented RED/GREEN TDD proof and a 5x flake-check on the new concurrency tests (dev handoff). I did not find any user-facing symptom of this new mechanism beyond what the reports already disclose (see the honest residual below). Required-still-passing journeys (J-01, J-03, J-05) replay clean; J-04 is SKIPPED, but this is a carried, pre-existing infra gap (Chrome MCP port 9224, documented since iter-18) unrelated to this iteration's diff — this iteration touches none of `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or `app/engine/warmup.py` (confirmed absent from the changed-file list), so it could not plausibly have caused or worsened that skip.

**Honest residual, not a regression but worth naming precisely:** while a historical date's background compute is in flight (~30s window), a concurrently issued `/backtest` request can transiently take 3.0–6.3s and `/api/health` up to 1.60s (`reports/perf-budgets.md` "Iteration 20"), versus a normal sub-second response. This is a **narrowing**, not a worsening, of the pre-iteration behavior (which was a 9.6–54s hard block with zero affordance for the SAME scenario) — nothing hangs, no page errors, and the readiness badge never drops (UT-07, live-verified). This is correctly flagged by every upstream report (perf-budgets.md, user-visible-changes.md, the pump note) as an advisory for the evaluator's performance-budget judgment, not a hidden defect — I confirm it is not silently omitted anywhere and it does not break any existing journey.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Gap? |
|---|---|---|
| Historical `/backtest` first-view no longer blocks the request thread (`ensure_historical_forward_aggregates_dispatched`) | Directly visible: page returns in ~0.08s instead of up to 54s, showing the honest interim state | None — full parity, live-verified |
| Corrected `refreshing`/`not_yet_computed` copy naming the real historical-dispatch cause | Rendered in place on `/backtest`, live-verified (screenshots above) | None |
| MCP `query_backtest` mirrors the identical dispatch fix (`apps/backend/app/mcp/tools.py`) | **No browser-page surface** — this is a non-browser, agent/tool integration channel; `apps/frontend/lib/api.ts` calls `GET /api/backtest` directly and never this MCP tool | Intentionally backend/tool-only, and **honestly disclosed as such** in `user-visible-changes.md`'s "Not Visible Yet" section and the ui-surface-map's "Backend-Only Changes" section — not silently hidden. Acceptable: this phase's goal does not imply a browser-facing delivery for the MCP channel. |
| New/updated backend tests (`test_forward_testing_serving_split.py`, `test_forward_testing_concurrency.py`, `test_api_backtest.py`) | No UI surface (test coverage only) | Expected — correctly classified as backend-only in the ui-surface-map |
| `reports/perf-budgets.md` "Iteration 20" measurement section | No UI surface (ops artifact) | Expected |

No gap between what was built and what is described as visible. The `implementation-summary.md`'s own "Backend-Only Items: None" claim checks out — the single user-facing improvement is fully wired into the existing page, and the one genuinely backend/tool-only piece (MCP) is transparently labeled as such rather than described as "complete" while quietly omitted from the UI narrative.

---

## Flags

### Hidden Capabilities
None. No new capability was introduced this iteration to hide.

### Undiscoverable Capabilities
None. The corrected copy is reachable via the same, unchanged 1-click sidebar path + the pre-existing as-of picker, and renders automatically with no extra interaction — live-verified via screenshot.

### Potential Regressions
None found. All components this iteration's diff touches (`RefreshingEvidenceBanner`, the `not_yet_computed` `EmptyState`, both confined to `apps/frontend/app/backtest/page.tsx`) belong to this feature's own iter-16→17→20 lineage, not a different feature's shared component. Navigation, `HealthBadge`, the Dashboard, and the Data Manager page are all untouched this iteration (confirmed via `git status`/`git log`) and their owning journeys (J-01, J-03, J-05) replay clean. J-04's SKIP is a carried, pre-existing infra gap (Chrome MCP wedge, documented since iter-18), not caused by this iteration's diff.

### Visual Consistency
Fully consistent — verified two ways:
1. **Raw diff review** (`git diff -- apps/frontend/app/backtest/page.tsx`): every hunk is either a code comment, a prop addition (`isLatest: boolean`), or a ternary on existing string literals. **Zero `className` changes, zero new Tailwind utility values, zero arbitrary hex/pixel values introduced** — the diff cannot have caused a visual-system deviation because it does not touch styling at all.
2. **Live screenshots**: both `UT-05-refreshing-banner.png` and `UT-02-historical-empty-state.png` show the `RefreshingEvidenceBanner` using the same amber/warn-toned `Card` treatment as the page's own pre-existing `SurvivorshipBanner` directly above it (same page, same visual family), and the `EmptyState` using the same dashed-border/muted-text component used elsewhere in the app (e.g. `ScorecardSection`). Typography scale, spacing, dark-theme palette, and badge/grade color-coding (leadership A/B/C/D/E grades, positive/negative green/red) are all consistent with the rest of the page and with prior-iteration screenshots. No arbitrary values found.

---

## Recommendation

No action required for this iteration's UI. Two items are worth carrying forward for the reviewer/auditor stage (not UX-regression blockers, noted here for completeness since they were flagged transparently by upstream artifacts):

1. `test_api_backtest.py`'s updated `test_backtest_evidence_is_as_of_scoped_expanding_window` (TC-11, AG-5 no-lookahead proof) was edited but not executed this session (~80-minute fixture, explicitly out of scope per the phase spec) — the dev handoff itself recommends the reviewer/QA stage run it with a larger time budget. This is a test-execution completeness item, not a UI/UX gap.
2. The transient 3.0–6.3s `/backtest` / up to 1.60s `/api/health` latency during a historical background-compute window (honest residual, `reports/perf-budgets.md` "Iteration 20") is a performance-budget question for the evaluator to weigh against the ≤1.5s committed budget — not a UX regression (nothing hangs, no journey breaks, strictly better than the pre-iteration 9.6–54s block it replaces).
