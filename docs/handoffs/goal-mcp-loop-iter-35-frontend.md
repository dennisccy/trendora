# goal-mcp-loop-iter-35 Frontend Handoff

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Agent:** developer
**Status:** BLOCKED — implementation complete, TypeScript typecheck/build NOT verified (environment
outage — see the "READ THIS FIRST" section of `docs/handoffs/goal-mcp-loop-iter-35-dev.md` for the full
explanation; the Bash tool stopped responding for the remainder of the session, so `npx tsc --noEmit` /
`next build` / browser verification could not be run). Code was written carefully against this project's
established patterns and manually re-read multiple times for syntax/type correctness, but that is not a
substitute for an actual compiler run — **do not treat this as a passing frontend build until one is run.**

## What Was Built

One new read-only card on `/data` (the Data Manager page): the live-vs-seed drift report (J-21 / backlog
B-304). It surfaces, from the SAME `GET /api/data` payload the page already fetches (no new network call),
whether the most recent Fetch/Expand job's overlap window agreed with the committed seed.

- **`apps/frontend/lib/api.ts`**: two new exported types —
  - `DriftAffectedSymbol { symbol: string; mismatching_dates: string[]; classification: string }`
  - `DriftReport { status: "clean" | "drift" | "unreadable"; reference: string | null; overlap_days:
    number | null; affected: DriftAffectedSymbol[] }`
  and an additive `drift: DriftReport | null` field on `DataOverviewResponse` (placed right after
  `capacity`, matching how that field was itself added in a prior iteration).

- **`apps/frontend/app/data/page.tsx`**: a new `DriftReportPanel({ drift })` component, placed right after
  `StorageCapacityPanel`'s definition and mirroring its exact `Card` + `PanelTitle` (with an explanatory
  hint tooltip) shape. Wired into the page's main render tree immediately after
  `<StorageCapacityPanel capacity={state.data.capacity} />`, reading `state.data.drift` — no new
  `useEffect`/fetch. Four states, each with its own `data-testid` for browser-qa:
  - **Absent** (`drift === null`, `data-testid="drift-status-absent"`) — quiet, `text-text-muted`: "No
    fetch has run yet — nothing to compare against the committed seed." Deliberately distinct wording from
    "clean" so an operator never confuses "never checked" with "checked and fine."
  - **Clean** (`data-testid="drift-status-clean"`) — quiet, `text-pos` with a small dot indicator: "The
    most recent fetch matched the committed seed over the last N common date(s)."
  - **Drift** (`data-testid="drift-status-drift"`) — LOUD: `border-warn bg-warn/10 text-warn` (the exact
    token combination `preflight-banner.tsx`'s `LoudBanner` uses for its `DEGRADED` state, per the plan's
    explicit instruction), an `AlertTriangle` icon, a summary line naming the affected-symbol count, then
    a list of every affected symbol with its exact mismatching dates and the "adjustment seam" label
    (`data-testid="drift-affected-{symbol}"` per row).
  - **Unreadable** (`data-testid="drift-status-unreadable"`) — the same loud amber treatment with an
    honest fallback message ("the artifact exists but could not be parsed... re-run a Fetch job").
  New icon import: `GitCompare` from `lucide-react` (added to the existing icon import block,
  alphabetized).

- **No proven-language anywhere** in the new card — it is purely descriptive integrity reporting (per
  B-304's explicit "must not introduce proven-language anywhere" and this iteration's binding acceptance),
  consistent with the rest of the anti-goal #1 discipline already enforced across this codebase's evidence
  surfaces.

## Confirmed unchanged (per the plan; verified by reading each file in full this session)

- `apps/frontend/components/preflight-banner.tsx` — already renders `preflight.reasons` as a generic
  bulleted list under a `DEGRADED`/`NO-GO` verdict; a new `"drift"` reason string from the backend's
  `compute_preflight` surfaces automatically with zero frontend change. Confirmed by reading the whole
  ~90-line file.
- `apps/frontend/components/readiness-provider.tsx` — not touched.
- `apps/frontend/app/layout.tsx` — not touched (the banner is already mounted once, cross-cutting).

## Design system compliance

- Component library: used `Card` (`@/components/ui/card`) and the page's own local `PanelTitle` helper —
  no raw HTML where a project component exists.
- Tokens only: `text-pos`, `border-warn`, `bg-warn/10`, `text-warn`, `text-text-muted`, `text-xs`,
  `font-semibold` — all pre-existing tokens already used elsewhere on this same page (`RebuildPanel`,
  `MacroFeedPanel`, `StorageCapacityPanel`); no arbitrary values introduced.
- States handled: absent / clean / drift / unreadable (four states, each with its own testid) — no bare
  happy-path-only render. There is no loading or per-card error state distinct from the page's own,
  because this card reads a field already present in the SAME `state.data` the page's top-level
  `loading`/`error`/`ok` states already gate (see `state.kind === "ok"` in `page.tsx`) — a second
  loading/error branch inside this card would be a duplicate, unnecessary state machine for data that is
  already guaranteed present-or-absent by the time this card renders.
- Responsive: the card is a plain block-level `Card` in the page's existing single-column vertical stack
  (matching `StorageCapacityPanel`'s placement) — no new breakpoint-specific layout was needed.

## Tests Run

No frontend test runner invocation was possible this session (see "Status" above). The backend tests that
exercise the exact payload shape this component consumes (`test_api_data.py`'s two new drift-field tests)
**were** run successfully (45/45 passed in that file) — see the dev handoff — which at least confirms the
JSON shape `DriftReportPanel` is written against is real and byte-matches the `DriftReport` TypeScript
type I authored.

## Known Issues

1. **No TypeScript compiler / build run this session** — the single biggest open risk on the frontend
   side. The code was re-read multiple times against the file's existing patterns and I am not aware of a
   type error, but this is unverified. Run `cd apps/frontend && npx tsc --noEmit` (or the project's usual
   check) before treating this as done.
2. **No browser/visual verification** — the four states (absent/clean/drift/unreadable) were designed by
   pattern-matching this page's existing `RebuildPanel` absent/present banner treatment and the
   `preflight-banner.tsx` `LoudBanner` token combination, but no screenshot or live render was taken.
3. Everything else needed for this frontend surface's correctness (the backend contract it reads) is
   covered by the backend verification status in the dev handoff — this is a pure read-only presentation
   layer with no client-side computation to independently break.
