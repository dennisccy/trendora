# goal-mcp-loop-iter-31 Frontend Handoff

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Agent:** developer
**Status:** complete

## What Was Built

- **New page `/research/graveyard`** (`apps/frontend/app/research/graveyard/page.tsx`) — a read-only table
  of every referee-REJECTED hypothesis (`FAIL` / `INSUFFICIENT`) across BOTH the canonical and staging
  certified-claims ledgers, reading ONLY `GET /api/research/graveyard`:
  - **Selectors** column — the claim's exact cohort selector-set as compact `key=value` chips (a page-local
    `SelectorChips`, mirrors the Registry page's own component of the same name — I copied the small
    presentational helper rather than extracting a shared one, consistent with how `/evidence`'s
    `ClaimHypothesis` and `/research/registry`'s `SelectorChips` already independently coexist in this
    codebase without a prior shared abstraction; extracting one now would mean touching those two
    unrelated pages, out of this iteration's scope).
  - **Verdict** column — a `Badge` in `danger` (FAIL) or `warn` (INSUFFICIENT) only, mirroring `/evidence`'s
    own `verdictVariant` mapping for these two statuses exactly. **Never `accent`** — the backend already
    filters PASS out, so this never collides with the Evidence page's "Proven" styling, but the guardrail
    is explicit in the code (`verdictKindVariant` has no `accent` branch at all). The verdict's `reason`
    text renders underneath, and a "permanent" pill (`Badge variant="default"`, mirrors the Registry page's
    own "backfill" pill styling) appears beside the verdict badge when the row's matched registration has
    `status === "closed"` (derived client-side from the already-served `lineage.status` — no new backend
    boolean).
  - **Date** column — `register_date` via the shared `formatIsoDate` helper.
  - **Deflation** column — `"{deflation} ÷{deflation_divisor}"` (e.g. `bonferroni ÷8`) when a numeric
    divisor is present, else the raw policy name alone (e.g. staging's `lord++` today carries
    `deflation_divisor: 1`, which still renders `lord++ ÷1` — verified against the real staging ledger
    data; a divisor-less future entry would render the bare name) — re-displays the referee's own recorded
    field verbatim, never recomputed.
  - **Ledger** column — a neutral `default`-variant pill reading `canonical` or `staging`.
  - **Lineage** column — a link to `/research/registry#registration-<id>` (carrying the global as-of param
    via `useAsOfHref`, consistent with every other in-app nav link) when the entry's selectors matched a
    registration; an honest "No registration lineage" text (no link) when they did not. Every real entry
    today matches (the iter-30 backfill is complete), so the honest-null path is exercised only via the
    backend fixture tests, not live data — expected and documented.
  - A **Revisit-protocol panel** (`id="revisit-protocol"`, a `Card` below the table) renders the served
    `revisit_protocol.rule` verbatim; each row carries a small "Revisit protocol →" same-page anchor link
    (a plain `<a href="#revisit-protocol">`, not a `next/link`, since it is an in-page scroll, not a
    navigation) so the spec's "each row links/anchors to it" is satisfied without duplicating the rule text
    per row.
  - Three explicit states: a loading skeleton, a fetch-error card ("Backend unavailable"), and an honest
    empty state (both ledgers absent/empty — should not occur today, but the page never crashes if either
    ledger file is ever missing/empty). Mirrors `/research/registry`'s three-state shell exactly, including
    the "Back to Research" link at the top (identical `useAsOfHref` wiring).
  - No forms, no edit/delete affordance anywhere — the graveyard is read-only, append-only history.

- **Research hub update** (`apps/frontend/app/research/page.tsx`) — a second card in the EXISTING
  "Governance & process" grid (the section iter-30 created and explicitly reserved this slot in), linking
  to `/research/graveyard`, `data-testid="research-governance-link-graveyard"` (the exact testid the spec
  names). Same card markup/hover/focus treatment as the existing registry card. The section's own header
  comment was updated from "(registry now; graveyard / budget / referee-audit to follow)" to "(registry +
  graveyard now, budget / referee-audit still to follow)" — a documentation-accuracy edit only, no
  structural/behavioral change.

- **`/research/registry` row anchor** (`apps/frontend/app/research/registry/page.tsx`, plan Assumption
  #4) — each `<tr>` gained `id={`registration-${row.id}`}` and a `scroll-mt-20` class (mirrors `/evidence`'s
  `ClaimRow` `id={anchorId}` + `scroll-mt-20` pattern exactly), so a graveyard Lineage link lands precisely
  on its backing registry row instead of just the top of the page. This is the one, narrow, explicitly-
  sanctioned presentation-only touch to an existing page (Assumption #4) — no data, computation, or
  behavior on that page changed.

- **`lib/graveyard.ts`** (new) — `GraveyardEntry` / `RevisitProtocol` / `GraveyardResponse` types, mirroring
  `lib/registry.ts`'s types-only pattern (`Verdict` is imported from `lib/evidence.ts` rather than
  redeclared, and `lineage` is typed as `PreRegistrationRow | null` imported from `lib/registry.ts` — no
  duplicate type definitions). No exported logic (nothing to unit-test — same rationale as `lib/registry.ts`
  carrying no companion test file).

- **`lib/api.ts`** — `fetchGraveyard(signal?)` calling `GET /api/research/graveyard`, following the exact
  shape of the existing `fetchRegistry`; re-exports the new graveyard types alongside the existing
  evidence/registry type re-exports.

## Design System Compliance

- Used the existing `Card`/`CardContent`, `Badge`, `PageHeading` components throughout — no raw HTML where
  a component exists.
- Table markup mirrors `/research/registry`'s table precisely (same border/spacing/typography tokens:
  `text-sm`, `text-xs uppercase tracking-wide text-text-faint` headers, `border-border`,
  `bg-surface`/`bg-surface-2`).
- No arbitrary colors/spacing — every class is an existing design-system token already used on the
  adjacent Registry/Evidence pages.
- No new visual effects introduced (no glow/gradient/glassmorphism) — a dense, calm, data-first table,
  consistent with the plan's Visual Requirements ("not a marketing surface").
- Hover/focus states on the new hub card and every link match the existing patterns exactly (same
  `hover:border-accent hover:bg-surface-2` / `focus-visible:ring-1 focus-visible:ring-accent` /
  `focus-visible:outline-none` classes, copy-consistent with the registry card and the evidence linkback).
- Responsive: the hub's governance grid is unchanged (`grid-cols-1 sm:grid-cols-2 xl:grid-cols-3`, now with
  a second card); the graveyard table wraps in `overflow-x-auto` (matches the registry/samples tables).

## Files Changed

- `apps/frontend/lib/graveyard.ts` -- NEW. Types only.
- `apps/frontend/lib/api.ts` -- added `fetchGraveyard`, re-exported graveyard types.
- `apps/frontend/app/research/graveyard/page.tsx` -- NEW. The graveyard table + revisit-protocol page.
- `apps/frontend/app/research/page.tsx` -- second governance-grid card; header comment updated.
- `apps/frontend/app/research/registry/page.tsx` -- row `id`/`scroll-mt-20` addition (Assumption #4).

## Tests Run

- `npx tsc --noEmit` -- clean, zero type errors, from `apps/frontend/`. One issue was caught and fixed
  during development: `DeflationLabel`'s `verdict` prop was initially typed as an ad-hoc
  `{ deflation?: unknown; deflation_divisor?: unknown }` shape, which TypeScript's "weak type" excess-
  property detection rejected when passed a real `Verdict` value (a `Verdict`'s explicit named properties
  don't include `deflation`/`deflation_divisor` even though its index signature technically allows them) —
  fixed by typing the prop as the real `Verdict` type directly instead of a shorthand inline shape.
- `next lint` -- not configured in this repo (no committed ESLint config; running it triggers an
  interactive first-time-setup prompt) — skipped, matching the iter-30 precedent.
- Live smoke test against a running `scripts/dev.sh` instance (backend :8255, frontend :3255):
  - `curl http://localhost:3255/research/graveyard` -> HTTP 200, no error markers.
  - `curl http://localhost:3255/research` -> HTTP 200, HTML contains
    `data-testid="research-governance-link-graveyard"` (the new hub card is server-rendered into the
    initial HTML).
  - `curl http://localhost:3255/research/registry` -> HTTP 200, no error markers (regression check on the
    Assumption #4 row-anchor edit).
  - `curl http://localhost:8255/api/research/graveyard` -> the full 14-entry payload, byte-inspected via
    Python: 7 canonical + 7 staging, all `FAIL`, all lineage-matched, `ma_stack` lineage `status ==
    "closed"`, `revisit_protocol.rule` present with the correct wording.
  - Frontend dev-server log shows clean compiles for every route touched, zero errors/warnings.
  - The table/row content itself (fetched client-side via `useEffect`, per this codebase's established
    "use client" + fetch-on-mount pattern) does not appear in a plain `curl` of the server-rendered shell —
    expected Next.js behavior for a client component's async data, not a bug. Interactive verification of
    the populated table, the `ma_stack` permanent pill in-frame, and the lineage link actually landing on
    the correct registry row is the browser-qa-agent's job downstream.
- No `lib/graveyard.test.ts` was written — the module carries only type declarations (no exported pure
  logic), matching `lib/registry.ts`'s own precedent (no companion test file for the same reason). The
  frontend's `node lib/*.test.ts` harness is separately non-functional in this sandbox regardless (see the
  dev handoff's Known Issues) — a pre-existing condition, reconfirmed this iteration, unrelated to any file
  I touched.

## Known Issues

See `docs/handoffs/goal-mcp-loop-iter-31-dev.md` — Known Issues (the Node TS-stripping environment gap,
no browser click-through performed by me, demo-narrator walkthrough is a downstream step). Nothing
frontend-specific beyond what that section already covers.
