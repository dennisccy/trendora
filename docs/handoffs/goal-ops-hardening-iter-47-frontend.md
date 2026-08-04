# goal-ops-hardening-iter-47 Frontend Handoff

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Agent:** developer
**Status:** complete

## What Was Built

The backend's cache-key/staleness fix for `GET /api/evidence` (see the main dev handoff for the full
backend story) chose **Path B (serve-stale-behind-a-label)**: when the server serves a previous generation
of a claim's `expectations` panel while a fresher one computes in the background, the response additively
carries `expectations_status: "refreshing"` on that claim. This requires a small, additive frontend change
so the Evidence page discloses that state honestly instead of rendering it identically to a fresh
("ready") panel.

- **`apps/frontend/lib/evidence.ts`** — `CertifiedClaim.expectations_status` type widened from
  `"unavailable"` (only) to `"unavailable" | "refreshing"`. `resolveDrawdownExpectationsPanelState` (the
  single, pure decision function `DrawdownExpectationsPanel` branches on — no React, no DOM, unit-testable
  under `node`) gains a 4th discriminated-union state, `{ kind: "refreshing"; expectations:
  DrawdownExpectations }`, distinct from `"present"` (current generation) and `"unavailable"` (no
  expectations at all). Resolution order: a claim with BOTH `expectations` and `expectations_status ===
  "refreshing"` resolves to `"refreshing"`; a claim with `expectations` and no/other status resolves to
  `"present"` (unchanged); a claim with no `expectations` but `expectations_status === "refreshing"` (an
  impossible-in-practice shape) resolves to `"absent"`, never fabricating a table with no payload.
- **`apps/frontend/app/evidence/page.tsx`** — `DrawdownExpectationsPanel` renders the table AS NORMAL for
  the `"refreshing"` state (the served values are real, honest, last-good-generation data — never a blank
  or loading placeholder) with one ADDITIVE element: a `Badge variant="warn"` reading "Refreshing" beside
  the panel heading, plus one added sentence to the existing descriptive paragraph explaining that a newer
  version is computing in the background. Reuses the EXISTING `Badge` component (already used elsewhere on
  this same page for phase labels) — no new component, matching the plan's Visual Requirements and the
  established `/backtest` `evidence_status: "refreshing"` precedent (a `Card` + spinner banner there; this
  page's claim-card layout is more compact, so a `Badge` — the SAME calm, factual, non-alarming warn-toned
  treatment — was the better fit for THIS surface, not a scaled-down copy of the other page's component).

## Visual Requirements Compliance

- Component patterns: reused the existing `Badge` component (`variant="warn"`, already used on this page)
  — no new component introduced.
- Layout: no layout change — the badge is additive inline next to the existing panel heading; the table
  structure, columns, and row rendering are byte-unchanged.
- Visual effects: none new — matches the existing evidence-status chip styling (calm, factual, never hype,
  per `docs/goal.md`'s Design Direction). The `warn` badge variant (amber/warn border+text, `bg-surface-2`)
  is the SAME token already used for other transient-state disclosures on this codebase.
- States handled: `ready` (unchanged — no badge, no status field), `refreshing` (NEW — badge visible, table
  still renders the honest last-good values), `unavailable` (unchanged — inline note, no table), `absent`
  (unchanged — panel renders nothing).

## New user-facing capability

None structurally new — no new page, route, or nav entry. The Evidence page's existing claim cards
additively disclose when a panel is showing a slightly-behind (but real, honest) generation instead of
silently looking identical to a fresh one. This closes a genuine (if narrow) AG-3-adjacent honesty gap: a
user could otherwise not know they were looking at pre-ingest data during the ~7-8 minute background
re-warm window after any dataset change.

## Files Changed

- `apps/frontend/lib/evidence.ts` — type + resolver (see above).
- `apps/frontend/app/evidence/page.tsx` — `DrawdownExpectationsPanel` badge rendering.
- `apps/frontend/lib/evidence.test.ts` — 4 new checks: `"refreshing"` resolves correctly and carries the
  payload verbatim; `"refreshing"` is distinct from both `"present"` and `"unavailable"`; the
  impossible-in-practice "status without payload" shape resolves to `"absent"`, never fabricating a table.

## Tests Run

```
cd apps/frontend
npx tsx lib/evidence.test.ts
  -> 49 evidence-badge resolver checks passed (45 pre-existing + 4 new)

npx tsc --noEmit
  -> clean, zero errors
```

## Live verification

Started via `scripts/start-frontend.sh` (prod mode, port 3255) against the live backend (port 8255).
`GET /` and `GET /evidence` both returned HTTP 200. The Evidence page is client-rendered ("use client"),
so a plain `curl` cannot show the fetched/rendered DOM — a real browser check (Chrome MCP) is the
`browser-qa-agent`'s role, not performed here. During this session's live backend drill, the REAL
`/api/evidence` response genuinely carried `expectations_status: "refreshing"` on all 7 claims for several
minutes (see the main dev handoff and `reports/perf-budgets.md` Item P) — the frontend code paths this
handoff describes were exercised by real traffic against real data, just not visually screenshotted by me.

## Known Issues

- No dedicated browser screenshot of the "Refreshing" badge state was captured by me (outside developer
  scope — the browser-qa-agent's role). The backend drill above confirms the REAL data shape exists and
  the frontend TypeScript compiles/resolves it correctly; a visual confirmation is still pending the QA
  lane. If the QA lane wants to reproduce the "refreshing" state deliberately, it needs a genuine
  `forward_returns` insert while a prior generation's `EventStudyCache` row exists (i.e., NOT immediately
  after a fresh boot) — inserting a single row and reloading `/evidence` within the ~7-8 minute re-warm
  window will show it live.
