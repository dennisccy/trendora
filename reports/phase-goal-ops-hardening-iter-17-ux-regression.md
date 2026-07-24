# Phase goal-ops-hardening-iter-17 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-PASS

This iteration's only user-visible surface is the existing `/backtest` page's evidence section. Every new
capability renders automatically on that already-1-click-reachable page (no new nav/route/control needed),
independent `git status` verification confirms zero diff in any shared global component (sidebar, health
badge, readiness provider, preflight banner, `/data` page), and the one browser-QA FAIL on record (UT-01)
is conclusively an operator-caused environment defect, not a code regression — confirmed both by the
operator's own root-cause write-up and by this review's own independent checks (below). Two small,
non-blocking observations are recorded under Recommendation, continuing directly from iter-16's own
UX-review follow-ups (both of which this iteration resolved).

---

## New Capability Discoverability

| Capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| Cross-`asof_key` last-good evidence (the load-bearing fix) — evidence section stays populated instead of going empty when the latest date's warm is still in flight | Sidebar "Backtest" (`apps/frontend/components/sidebar.tsx:37`, unmodified this iteration) → `/backtest`, bottom evidence section | 1 click | N/A — this is an absence-of-failure (no empty state where one used to appear), nothing to label | Confirmed live for the sibling same-`asof_key` stale-version case (`TC-07-refreshing-banner-with-asof.png`); the genuine cross-date case is unproven live this session — see UI vs Backend Parity |
| `evidence_asof` label in `RefreshingEvidenceBanner` | Same 1-click path; renders automatically inside the existing banner, no extra click/toggle | 1 click | Clear: "...the last complete version — evidence as of `2026-07-22`, generated `2026-07-23 21:56:07`..." — plain date text, directly comparable to the "Viewing as-of `<date>`" badge already at the top of the same page | Confirmed live — verified by direct image read of `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png`: the amber/warn `Card` shows the new date text exactly where the diff places it, immediately before "generated" |
| Reworded `not_yet_computed` `EmptyState` copy | Same 1-click path; renders in place of the evidence section automatically | 1 click | Improved: no longer uses "ingest" (a term with no in-app match, flagged by iter-16's own UX review); now reads "Backfilling or fetching data that covers it..." — recognizable verbs that echo `/data`'s actual job-kind labels ("Backfill snapshots" / "Fetch EOD prices") | Confirmed live — verified by direct image read of `TC-09-not-yet-computed-state.png`: dashed-border card, flask icon, exact new copy, no duplicated title |

All three items require **zero additional clicks or navigation** beyond the pre-existing "Backtest" sidebar
entry — this is a correctness/disclosure fix to a page users already visit, not a new capability that needs
discovering. `git status --porcelain` (checked independently, not only cited from the handoffs) confirms
`apps/frontend/components/sidebar.tsx` has zero changes this iteration — the nav entry, its position, icon,
and label are byte-identical to before. No "hidden capability" or "undiscoverable capability" applies.

**Label clarity note (continuity from iter-16):** iter-16's own UX-regression review flagged the previous
`not_yet_computed` copy's use of "ingest" as unmatched jargon and recommended naming the actual in-app
affordance. This iteration's new copy ("Backfilling or fetching data that covers it will compute this
evidence") substantially resolves that — it now uses the same verbs `/data`'s job form uses — though it
stops short of literally naming the "Data Manager" page or linking to it (the phase spec explicitly ruled
out adding a new link/control: "New user actions: none"). This is a minor residual, not a fresh flag; see
Recommendation.

---

## Regression Risk

Per the `ui-regression-scout` skill's method — components this iteration's `ui-surface-map.md` touches,
cross-referenced against every component prior-phase handoffs describe as load-bearing for a Must-have
journey. All risk levels below were checked directly against `git status --porcelain` output (not only the
dev/frontend handoffs' self-report).

| Shared component | Prior feature it serves | This iteration's change | Regression risk |
|---|---|---|---|
| `apps/frontend/components/empty-state.tsx` (`EmptyState`) | Widely shared — ~14 pages/components call it: Themes, Watchlist, Methodology (×2), Sectors, Scanner Runs (×2), Stocks (×2), Data Manager (×4), `research/severity-velocity`, `research/samples` (×2), `availability-heatmap`, `evidence-panels`, plus `/backtest`'s own `ScorecardSection` empty state | **Zero changes to the component itself** (confirmed: `empty-state.tsx` does not appear in `git status --porcelain`'s modified-file list). Only the `description` string literal passed at ONE call site (`/backtest`'s `not_yet_computed` branch, `page.tsx:238`) changed | **None for all other ~13 call sites** — the component's props/render contract is untouched, so Themes/Watchlist/Data-Manager/Stocks/etc.'s own empty states cannot be affected. **Low, verified-safe** for `/backtest`'s own two call sites (this one changed; the sibling `ScorecardSection` one, visible unchanged in both evidence screenshots, is untouched). |
| `RefreshingEvidenceBanner` (local function, `apps/frontend/app/backtest/page.tsx:270`) | J-08 (introduced iter-16) | Confirmed page-local, single call site (`grep -rn "RefreshingEvidenceBanner"` returns exactly 2 lines: the definition and its one call). Purely additive: new `evidenceAsof` prop added; the existing `generatedAt` prop/rendering is byte-unchanged | **None elsewhere** (not exported, not imported anywhere else). **Low** for its own iter-16 usage — confirmed by screenshot that the pre-existing heading, warn styling, `Loader2`, and generation-timestamp text all still render exactly as before, with the new date text purely inserted alongside. |
| `BacktestResponse` interface (`apps/frontend/lib/api.ts`) | J-06/J-07 (this endpoint's own budget/health), and the sole frontend consumer of this interface | Diff is a pure addition: one new optional-typed field `evidence_asof: string \| null` plus a doc comment (confirmed via `git diff` — no other line in this 1000+ line file touched). Frontend handoff's own grep, independently spot-checked, found no other file references `evidence_status`/`evidence_generated_at`/`evidence_asof` outside `lib/api.ts` and `app/backtest/page.tsx` | **None** — an additive TS interface field cannot break any other consumer since none exists. |
| Sidebar/nav (`apps/frontend/components/sidebar.tsx`) | Every page's reachability — J-01 through J-08's homes | **None** — confirmed absent from `git status --porcelain`'s modified-file list | **None.** |
| Global readiness/health chain (`components/readiness-provider.tsx`, `components/health-badge.tsx`, `components/preflight-banner.tsx`) | **J-04** ("Non-blocking boot with visible status") — rendered on every page | **None** — confirmed absent from `git status --porcelain`'s modified-file list | **None from this iteration's code.** See below for the browser-QA FAIL this chain produced this session, which is an environment issue, not a code regression. |
| `/data` page (`apps/frontend/app/data/page.tsx`) | **J-01** ("Backfill honors the requested range"), **J-03** ("No per-run range cap") | **None** — confirmed absent from `git status --porcelain`'s modified-file list | **None.** |

**On the browser-QA FAIL (UT-01, "Backend unavailable"/NO-GO):** this review independently re-verified the
operator's own root-cause finding rather than taking it at face value. Two checks performed directly by
this review:
1. `git status --porcelain` lists exactly 7 modified product files this iteration (`apps/backend/app/api/backtest.py`, `apps/backend/app/engine/forward_testing.py`, `apps/backend/app/mcp/tools.py`, two backend test files, `apps/frontend/app/backtest/page.tsx`, `apps/frontend/lib/api.ts`) plus `reports/perf-budgets.md`. None of the four files the browser-QA agent's in-page `window.fetch` instrumentation implicated (`readiness-provider.tsx`, `health-badge.tsx`, `preflight-banner.tsx`, `app/data/page.tsx`) appear in that list.
2. `grep -rlo 'localhost:18255' apps/frontend/.next` (run directly by this review, not copied from the operator's note) returns **no matches** — the rebuilt `.next` output the operator produced after killing the colliding second dev server is clean.

Both checks corroborate the operator's conclusion: the permanent NO-GO/"Backend unavailable" state UT-01
hit in its literal, unpatched form was caused by two Next.js dev servers sharing one `.next` build directory
(inlining the throwaway backend's `NEXT_PUBLIC_API_URL` into the main app's compiled chunks), not by any
line this iteration or any prior iteration shipped. **No "potential regression" flag applies to J-04 or any
required-still-passing journey's surface.**

**Live-state finding at review time (for the operator, per their own request):** at the moment this review
ran, `curl`/`ss`/`ps` all show the main backend (`:8255`) and main frontend (`:3255`) are **not currently
reachable** — connection refused, no matching process in `ps aux`, and `ss -tlnp` shows only the throwaway
backend (`:18255`, pid 1245537) still listening. This contradicts the pump note's "both up and healthy"
status as of this review's start. Per the pump note's own instruction, this review did not attempt to start
or stop anything; it is reported here for the operator to act on. This finding does not change the verdict
above — all the evidence this review relies on (screenshots, DOM captures) was gathered by browser-QA while
the services were up, and this review's source-level checks (`git status`, `git diff`, component/prop
inspection) do not require a live server — but it does mean this review could not perform its own fresh
live re-verification beyond what QA already captured.

---

## UI vs Backend Parity

| Backend capability (this iteration) | Surfaced in UI? | Where |
|---|---|---|
| Cross-`asof_key` fallback search (`resolved_forward_aggregate_evidence` widened to older `asof_key`s) | **Yes, code-complete** | The whole `/backtest` evidence section renders the fallback's result exactly as it renders any other `refreshing`/`ready` result — no special-case UI branch needed since the resolver returns the same shape either way |
| `evidence_asof` field on `GET /api/backtest` | **Yes** | `RefreshingEvidenceBanner`'s new date text (confirmed live via screenshot for the same-`asof_key` stale-version case) |
| `evidence_asof` on MCP `query_backtest` | **No browser surface — by design, not a gap.** MCP tools serve AI-agent/Model-Context-Protocol clients, not this Next.js frontend; no page in this app renders any MCP tool's output (an established pre-existing pattern, not new to this iteration). Correctly logged as "Not Visible Yet" rather than omitted. |
| B5 (historical branch's duplicate read/deserialize removed) | **No UI surface, and none is warranted** — byte-identical output, purely an internal efficiency change a user cannot perceive |
| B3 (`evidence_generated_at` gains a UTC designator) | **No new UI surface needed** — the field is still rendered through the same `formatIsoDateTime` helper; the serialized form is an implementation detail, not a display difference |
| Reworded `not_yet_computed` copy (F2/F3) | **Yes** | Confirmed live via screenshot |

**One genuine, honestly-disclosed gap, correctly categorized:** the cross-`asof_key` fallback — this
iteration's actual "load-bearing fix" — has **not been exercised live end-to-end in a browser this
session**. `user-visible-changes.md`'s own "Not Visible Yet" section states this plainly, and the dev
handoff's operator-results section explains why: the working database's latest trading day
(`2026-07-22`) has no future day to backfill into (this project makes no live external data calls, AG-9),
so the exact triggering shape cannot be produced without fabricating data. The substitute the operator
tried healed via the pre-existing historical create-once carve-out instead. **This is not a UI
discoverability gap** — the banner's rendering code path is proven live for the sibling same-`asof_key`
case (identical `evidenceAsof` prop, identical `formatIsoDate` call), and the fallback logic itself is
proven by 5 passing backend unit tests (TC-1/2/4/5/6) plus a clean `tsc --noEmit`. It is an evidence-
completeness question for the auditor/evaluator (AG-3/AG-5 correctness territory), not a "backend
capability hidden from the UI" question — the UI is wired and ready; the specific data condition to see it
fire just has not occurred yet. Flagged here for visibility per this review's own remit to compare
`implementation-summary.md` against `user-visible-changes.md`, not as a discoverability defect.

**Documentation-freshness aside (not a product issue):** `reports/phase-goal-ops-hardening-iter-17-implementation-summary.md`
still lists TC-8/TC-9 as fully outstanding ("Incomplete Items"/"Known Limitations"), written before the
operator's pass; the dev/frontend handoffs carry the later "UPDATE (2026-07-24, operator pass)" annotations
this review relied on instead. Worth a sync in a future pass, not a UX defect.

---

## Flags

### Hidden Capabilities
None. Every new capability renders automatically on the already-1-click-reachable `/backtest` page.

### Undiscoverable Capabilities
None requiring >2 clicks or obscure navigation.

### Potential Regressions
None found. `EmptyState`'s ~13 other call sites, `RefreshingEvidenceBanner`'s own iter-16 usage, the
sidebar/nav, and the entire J-04/J-01/J-03 global-health and `/data`-page surface were all checked directly
against `git status --porcelain` (not only the handoffs' self-report) and show zero footprint from this
iteration. The one FAIL on record (browser-QA's UT-01) is independently confirmed, by this review's own
`git status` + `grep` checks (not just the operator's narrative), to be a Next.js build-directory collision
from a second dev server the operator ran from the same cwd — not a line of product code this or any prior
iteration shipped.

### Visual Consistency
- Exact token/pattern reuse, verified directly in the diff: the new `evidenceAsof` date is wrapped in
  `<span className="num">`, the identical class already wrapping the neighboring `generatedAt` timestamp in
  the same sentence — not a new pattern. `RefreshingEvidenceBanner`'s `border-warn`/`text-warn`/
  `text-text-muted` classes and its `Card` + `Loader2` structure are entirely unchanged from iter-16. No new
  component was introduced; `EmptyState` is reused via its existing `icon`/`title`/`description` props with
  no styling change.
- Both live screenshots (`TC-07-refreshing-banner-with-asof.png`, `TC-09-not-yet-computed-state.png`)
  confirm this in situ: the amber-toned refreshing banner matches the sibling `SurvivorshipBanner` directly
  above it on the same page, and the reworded empty state matches the SAME dashed-border/flask-icon pattern
  visible one section up in the same screenshot (`ScorecardSection`'s own empty state), with no visual
  drift between the two `EmptyState` uses.
- No arbitrary hex/pixel values were introduced; no new spacing/typography scale appears in the diff.

---

## Recommendation

No blocking action required.

1. **Capture TC-8's live cross-`asof_key` scenario the next time a real trading day naturally advances** —
   this is the one part of the load-bearing fix with no live browser proof this session (unit-tested only).
   Low urgency: the rendering code path is already proven live for the sibling same-key case, and the
   resolver logic is proven by 5 passing unit tests including a no-lookahead SQL-inspection test (TC-5).
2. **Optional, cosmetic:** if a future iteration touches the `not_yet_computed` copy again, consider
   explicitly naming "Data Manager" (the sidebar label) rather than only echoing its job-kind verbs
   ("Backfilling or fetching") — closes the residual sliver of iter-16's original label-confusion flag.
   Not blocking; the jargon term ("ingest") iter-16 actually flagged is already gone.
3. **For the operator:** the main backend (`:8255`) and main frontend (`:3255`) are not reachable as of
   this review (connection refused; only the throwaway `:18255` backend is still listed in `ps`/`ss`). Per
   your own instruction, no start/stop was attempted by this review.
4. Sync `reports/phase-goal-ops-hardening-iter-17-implementation-summary.md`'s "Incomplete Items"/"Known
   Limitations" sections with the dev handoff's later operator-pass results (documentation freshness only,
   not a product gap).

Positive continuity note: this iteration directly closed both of iter-16's own UX-regression follow-ups —
the "ingest" jargon is gone from the empty-state copy, and the `not_yet_computed` state now has its
first-ever live browser screenshot (`TC-09-not-yet-computed-state.png`).
