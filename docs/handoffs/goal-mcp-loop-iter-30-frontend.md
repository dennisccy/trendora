# goal-mcp-loop-iter-30 Frontend Handoff

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Agent:** developer
**Status:** complete

## What Was Built

- **New page `/research/registry`** (`apps/frontend/app/research/registry/page.tsx`) — a read-only table
  of every pre-registered hypothesis, reading ONLY `GET /api/research/registry`:
  - **Selectors** column — each registration's exact cohort selector-set rendered as compact `key=value`
    chips (a page-local `SelectorChips` component, mirroring the `/evidence` page's `ClaimHypothesis`
    presentation — array values like a combination's `condition` legs join with `+`).
  - **Rationale** column — the registered hypothesis's economic rationale, verbatim.
  - **Registered** column — the registration date, formatted via the shared `formatIsoDate` helper.
  - **Source** column — provenance text (e.g. "proposer-guidance.md §4.1 #2; certified-claims.jsonl
    entry 5 (promoted, ledger:canonical); staging-ledger.jsonl entry 2"), verbatim.
  - **Status** column — a `Badge` in the **`default` (neutral/muted)** variant, deliberately NOT the
    accent/danger PASS/FAIL coloring the Evidence page uses for proven-ness, since "registered" /
    "tested" / "closed" is a descriptive process state, not a proven/not-proven signal (a "tested" row can
    have FAILED out-of-sample — every row does today). Backfilled rows carry an additional small
    "backfill" pill beside the status.
  - Three explicit states: a loading skeleton, a fetch-error card ("Backend unavailable"), and an honest
    empty state (should not occur post-backfill, but the page never crashes if the registry file is ever
    absent/empty).
  - A "Back to Research" link at the top, matching `research/samples/page.tsx`'s exact pattern (same
    `useAsOfHref` wiring, same icon/label).
  - No forms, no edit/delete UI anywhere — registrations are appended by the gate/tooling only.

- **Research hub update** (`apps/frontend/app/research/page.tsx`) — a new "Governance & process" section
  below the existing ten-lab grid, with one card linking to `/research/registry` (via `useAsOfHref`, same
  as every other hub link, so the as-of date carries through). The existing `RESEARCH_LABS` array
  (`lib/research-labs.ts`) — a J-113 fixed reading-order contract over the ten analytical labs — was left
  completely untouched; the governance link lives in a separate, visually distinct section written
  directly in the hub page. This establishes the pattern the three forthcoming governance pages
  (graveyard / budget / referee-audit) are expected to reuse.

- **`lib/registry.ts`** (new) — `PreRegistrationRow` and `RegistryResponse` types, mirroring
  `lib/evidence.ts`'s types-module pattern. No exported logic (nothing to unit-test — see Known
  Limitations in the dev handoff for why no `lib/registry.test.ts` was added).

- **`lib/api.ts`** — `fetchRegistry(signal?)` calling `GET /api/research/registry`, following the exact
  shape of the existing `fetchEvidence`; re-exports the new types alongside the existing evidence-type
  re-exports.

## Design System Compliance

- Used the existing `Card`/`CardContent`, `Badge`, `PageHeading` components — no raw HTML where a
  component exists.
- Table markup mirrors `app/research/samples/page.tsx` precisely (border/spacing/typography tokens: `text-sm`,
  `text-xs uppercase tracking-wide text-text-faint` headers, `border-border`, `bg-surface`/`bg-surface-2`).
- No arbitrary colors/spacing — every class is an existing design-system token already used elsewhere in
  the Research section.
- No new visual effects introduced (no glow/gradient/glassmorphism) — this is a dense, calm, data-first
  table, consistent with the plan's Visual Requirements ("not a marketing surface").
- Hover/focus states on the new hub card match the existing lab cards exactly (same `hover:border-accent
  hover:bg-surface-2` / `focus-visible:ring-1 focus-visible:ring-accent` classes, copy-consistent).
- Responsive: the hub's governance grid uses the same `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` as the
  existing lab grid; the registry table wraps in `overflow-x-auto` (matches the samples table).

## Files Changed

- `apps/frontend/lib/registry.ts` -- NEW. Types only.
- `apps/frontend/lib/api.ts` -- added `fetchRegistry`, re-exported registry types.
- `apps/frontend/app/research/registry/page.tsx` -- NEW. The registry table page.
- `apps/frontend/app/research/page.tsx` -- new "Governance & process" section.

## Tests Run

- `npx tsc --noEmit` -- clean, zero type errors, from `apps/frontend/`.
- `next lint` -- not configured in this repo (no committed ESLint config; running it triggers an
  interactive first-time-setup prompt) — skipped, matching the project's current state; not something
  this iteration should introduce unprompted.
- Live smoke test against a running `scripts/dev.sh` instance (both prod-adjacent dev services, backend
  on :8255, frontend on :3255):
  - `curl http://localhost:3255/research/registry` -> HTTP 200, HTML contains "Pre-registration registry".
  - `curl http://localhost:3255/research` -> HTTP 200, HTML contains "Governance" and "Pre-registration
    registry" (the new hub card is server-rendered into the initial HTML).
  - `curl http://localhost:3255/evidence`, `/stocks` -> HTTP 200 (no regression in adjacent pages).
  - Frontend dev-server log shows clean compiles for every route touched (`✓ Compiled /research/registry
    in 2.6s (722 modules)`, `✓ Compiled /research in 499ms`), zero errors/warnings.
- No `lib/registry.test.ts` was written — the module carries only type declarations (no exported pure
  logic), matching the codebase's own convention that only `lib/*.ts` files with actual pure functions get
  a companion `*.test.ts` (compare `lib/api-base.ts`/`lib/dates.ts`, which also have no logic beyond
  simple re-formatting and are tested elsewhere or not at all). The frontend's `node lib/*.test.ts` harness
  is separately non-functional in this environment regardless (see the dev handoff's Known Issues) — a
  pre-existing condition unrelated to this file.

## Known Issues

See `docs/handoffs/goal-mcp-loop-iter-30-dev.md` — Known Issues (row-count discrepancy, no browser
click-through performed by me, demo-narrator walkthrough is a downstream step). Nothing frontend-specific
beyond what that section already covers.
