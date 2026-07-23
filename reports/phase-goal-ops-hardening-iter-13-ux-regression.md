# Phase goal-ops-hardening-iter-13 — UX Regression Review

**Date:** 2026-07-23

**Verdict:** UX-REGRESSION-PASS

This iteration is a backend-only latency fix (`IndexSeriesCache`, an ingest-time-warmed cache for the
single unparameterized default `GET /api/indexes?full=true` hot key). Confirmed independently via
`git status`/`git diff --stat HEAD`: zero files under `apps/frontend/` appear in the diff — only
`apps/backend/app/{models.py,api/indexes.py,engine/indexes.py,engine/data_manager.py}` plus three backend
test files changed. No new capability, page, button, form field, or nav entry was added or could have been
added (`plan.md`'s own "UI Evolution" section and `user-visible-changes.md`'s "What Users Can Now Do" both
say "none," and this matches the actual diff). The canonical real-Chrome control measurement this iteration
exists to produce came back decisively within budget. Two non-blocking items are flagged below for the
record — neither is caused by this iteration and neither gates its verdict.

---

## New Capability Discoverability

No new capability was shipped this iteration — discoverability assessment does not apply. The only
observable effects are (1) faster load of an already-existing, already-wired call, and (2) one new legal
value ("index series") in an already-generic, already-rendered comma-separated list. Neither is a "new
capability" in the navigation-path sense; both are covered under UI vs Backend Parity below instead.

---

## Regression Risk

### `PhaseCrossViewCard` — Dashboard (`/`), on-mount `GET /api/indexes?full=true` call

**Prior feature served:** the phase/regime cross-view chart (home page, 0 clicks) — the same live component
verified in iter-6's own regression pass.
**Current change:** none to the component itself (confirmed `git diff --stat` empty for this file); only the
backend response for its unparameterized on-mount request is now served from a warmed cache instead of
recomputed.
**Risk assessed:** Low, and independently closed by real-browser evidence — UT-04 measured one fresh-nav
load at **70.5ms** (budget ≤1500ms), chart and tooltip both populated, as-of `2026-07-17` shown, no
StrictMode double-fire. UT-06 confirms the tooltip's regime/phase/severity/P(bear) fields are fully
populated (no "N/A"), matching pre-iteration content. The developer's own live byte-identity check
(`direct == api → True`, full dict equality including `asof_date` and all 10 `series` entries) rules out a
silent content regression from the cache path.

### `IndexVendorPanel` — Data Manager (`/data`), on-mount `GET /api/indexes?full=true` call

**Prior feature served:** the vendor-disclosure table (10 rows, one per configured index symbol).
**Current change:** same backend-only routing change as above; component itself untouched.
**Risk assessed:** Low, closed by evidence — UT-03 measured **three** independent fresh-nav loads at
218.7ms / 218.7ms / 219.2ms (≤1500ms budget, ~7x margin), host `load1` 0.36–0.69 confirming an idle-host
reading, and the vendor table byte-identical across all three loads. UT-05 confirms every one of the 10
rows still shows a named vendor or an honest "—", no blanks — matching the pre-iteration content contract.

### `BackfillBreakdown` ("Refreshed: ..." line) — three render sites on `/data`

**Prior feature served:** the ingest-aggregate summary line, added in ops-hardening iter-1, already rendered
generically (`aggregatesRefreshed.map(a => a.replace(/_/g, " ")).join(", ")`) across the live Job progress
panel, the persisted Last Run Summary card, and the Run History table's per-row cells.
**Current change:** the backend can now legally include one new item, `"index_series"`, in this array when
its warm step actually persists a row that run. No frontend file changed — the existing generic renderer
picks it up automatically.
**Risk assessed:** Low. UT-08/UT-09 could not exercise the "present" case live this session (the
developer's own diagnostic API call self-healed the cache before the ingest job's own turn ran, so the
job's warm step found an already-fresh row and correctly omitted "index series" — a HIT, not a bug). UT-09
did confirm the honest-omission side broadly: 0 of 41 visible Run History rows fabricate "index series",
including a run that genuinely didn't touch a configured index symbol's bars. This leaves the positive
("index series" present and styled identically to sibling items) case SKIPPED rather than PASSED — a gap in
QA evidence, not a demonstrated defect, and the underlying gating logic is unit-tested
(`test_data_manager.py -k index_series`, 30 passed per the dev handoff).

### J-04 (Non-blocking boot with visible status) — not re-verified this iteration

**Prior feature served:** the global readiness badge, preflight banner, and interrupted-job Run History
state (health-badge.tsx, preflight-banner.tsx, backed by `health.py`/`readiness.py`/`main.py`/`warmup.py`).
**Current change:** none — all of these files are explicitly named in the plan's "Out of Scope" /
"do not redo" list and confirmed untouched by the diff.
**Risk assessed:** Low by code-diff (nothing this journey depends on changed), but the fresh-evidence
posture is weaker than iter-12's own precedent: iter-12 partially re-verified J-04 live (2/6 steps freshly
confirmed via log/DOM reads) and explicitly reasoned that the remaining steps carry forward safely because
the rendering/backend files were diff-empty. This iteration's UT-J-04 is a flat SKIP in both the browser-qa
merge and the deterministic regression replay — "5 of 6 steps require a live backend restart or kill, which
I am explicitly instructed not to perform myself this run" — with no equivalent diff-empty carry-forward
reasoning written down. This is a QA-evidence completeness gap against the plan's own TC-8 ("J-01/J-03/
J-04/J-05 re-verified... all four recorded passing"), not an observed or plausible product regression: the
same permission constraint (agents cannot start/stop services this session) applied to iter-12 too, and the
files this journey depends on are unchanged. Flagged for the record; does not change this iteration's
verdict since it reflects an unexercised test, not a failing one, on unmodified code.

### Other shared surfaces checked, no risk

- `apps/backend/app/engine/forward_testing.py` — confirmed byte-unchanged (TC-12); the AG-8 MemoryError at
  line 826 reproduced once during the developer's own live verification, but this is a documented,
  owner-scoped, pre-existing issue since iter-8, correctly isolated (job completed `status: "ok"`,
  `"forward_aggregates"` honestly absent from `aggregates_refreshed`), and out of scope for this iteration.
  Not a new regression.
- Navigation/sidebar/layout components: not in the diff, no navigation-path change to check.
- `blueprint.md`: bookkeeping-only additions per the plan (new cache row, new enum member name); no row's
  producer/endpoint/module changed in a way that affects a UI surface.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Status |
|---|---|---|
| `IndexSeriesCache` table, index-scoped dataset-version stamp, ingest-warm step | None by design — pure backend infrastructure, no page/panel/setting exposes the cache directly | Correctly scoped as "Not Visible Yet" in `user-visible-changes.md`; this is a latency mechanism, not a feature requiring its own UI |
| Faster `GET /api/indexes?full=true` hot-key response | Same two components (`PhaseCrossViewCard`, `IndexVendorPanel`), same displayed values, only faster | Confirmed byte-identical content; confirmed faster by real-browser measurement (UT-03/UT-04) — parity holds, no gap |
| `"index_series"` legal value in `aggregates_refreshed` | Already-generic `BackfillBreakdown` renderer picks it up with zero frontend change | Correctly scoped; positive-case rendering unverified live this session (see Regression Risk above) but not a parity gap — the rendering code path is identical to the other six already-shipped items |
| Non-default `range`/explicit historical `as_of` index queries (pre-existing backend capability, unchanged by this iteration; TC-6 reconfirms it stays on the lazy uncached path) | **No live UI element anywhere requests anything other than the default range.** Neither `PhaseCrossViewCard` nor `IndexVendorPanel` ever passes a `rangeKey` to `fetchIndexes` (grep-confirmed: only the one file that does, `major-indexes-card.tsx`, is dead code — 0 imports outside itself, last touched under a different, earlier goal session, superseded by `PhaseCrossViewCard` in ops-hardening iter-6) | **Pre-existing parity gap, not caused by this iteration** — see Flags below |

---

## Flags

### Hidden Capabilities

- **Index-chart range-preset selection has no live UI affordance anywhere in the product.** The backend
  supports (and this iteration's own TC-6 re-confirms unchanged) an explicit non-default `range` parameter
  on `GET /api/indexes`, and browser-qa's UT-07 attempted to exercise it via `document.querySelectorAll('[aria-label="Range preset"]')`
  — 0 matches on either live page. Source-grep confirms the only frontend file that ever passes a `rangeKey`
  to `fetchIndexes` is `major-indexes-card.tsx`, which is unreachable dead code (0 imports outside its own
  file; `git log --follow` shows it was last modified under a different, older goal session and superseded
  by `PhaseCrossViewCard` in ops-hardening iter-6, which never carried the range-selector UI forward). This
  predates iter-13 by several iterations and is **not** caused by this iteration (zero frontend files
  touched; the plan's own scope explicitly excludes anything but the default-range hot key). It is flagged
  here because this is the first iteration whose own test plan attempted to exercise it and surfaced the
  gap — no prior `ux-regression.md` in this session (iter-1 through iter-12) mentions "Range preset" or
  `major-indexes-card`. Recommend a backlog note: either wire a range selector into `PhaseCrossViewCard`/
  `IndexVendorPanel`, or delete `major-indexes-card.tsx` and its now-stale UT-07 test case so future test
  plans stop asserting against dead code. Does not gate this iteration's verdict.

### Undiscoverable Capabilities

- None new this iteration.

### Potential Regressions

- None confirmed. Both live components that consume the changed endpoint (`PhaseCrossViewCard`,
  `IndexVendorPanel`) were re-verified with fresh real-browser evidence and are byte-identical in content,
  only faster. See Regression Risk above for J-04's weaker (but not failing) re-verification posture this
  cycle, and the pre-existing AG-8 MemoryError disclosure — both are watch items, not regressions caused by
  this iteration.

### Visual Consistency

- No new pages or components were added, and no existing component's JSX/markup changed (confirmed by
  diff — only backend routing/caching logic changed). Nothing to check against DESIGN SYSTEM tokens this
  iteration; the two affected components render their exact pre-existing loading/content/tooltip states
  verbatim, confirmed unchanged by UT-01/UT-02/UT-05/UT-06.

### Process / Test-Plan Notes (non-blocking, flagged for the evaluator)

- **UT-07's `FAIL` is a stale test-plan defect, not a product regression.** It asserts against
  `major-indexes-card.tsx`'s `aria-label="Range preset"` dropdown, which does not exist on any live page
  (see Hidden Capabilities above). The underlying backend behavior it was meant to probe (a non-default
  range request) was independently confirmed correct via a direct `fetch()` call (200, 661ms, 10 series).
  This FAIL should not be read as evidence of a user-facing defect introduced by iter-13.
- **UT-08/UT-09/UT-10 (the positive "index series" appears/reads clearly cases) are SKIPPED, not PASSED**,
  because the live session's own diagnostic reads self-healed the cache ahead of the one ingest job
  submitted this turn. The gating logic itself is unit-tested and green; only the live-UI rendering of the
  new string was left unobserved this cycle. Recommend a future iteration's QA pass submit a bounded
  backfill that lands a genuinely new bar for a configured index symbol (rather than re-triggering a
  same-day, already-covered date) to close this specific evidence gap.

---

## Recommendation

No blocking action required for this iteration. Two non-blocking backlog items for the evaluator/owner:
1. Decide the fate of `major-indexes-card.tsx` (wire its range-selector UI into a live page, or delete the
   dead file and its associated stale UT-07 test case) — a real, if long-standing and non-urgent, UI/backend
   parity gap, not created by this iteration.
2. When a future iteration next runs an ingest job that lands a genuinely new bar for a configured
   `index_chart` symbol, use that opportunity to close the still-open positive-case evidence gap for
   "index series" appearing in the `BackfillBreakdown` line (UT-08/09/10).
