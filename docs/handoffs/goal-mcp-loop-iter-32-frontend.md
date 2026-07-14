# goal-mcp-loop-iter-32 Frontend Handoff

**Phase:** goal-mcp-loop-iter-32
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

- **New page `/research/budget`** (`apps/frontend/app/research/budget/page.tsx`) — a read-only
  certification-budget accounting panel reading ONLY `GET /api/research/budget`:
  - A **four-card grid** (`data-testid="budget-grid"`, `sm:grid-cols-2 xl:grid-cols-4`), one card per
    figure named in the spec: **Total trials to date** (`n_trials_to_date` + "next trial will be #N"
    subtext), **Current canonical required p** (formatted via the existing `formatPValue` helper from
    `lib/evidence.ts`, plus a "= 0.05 ÷ 8 (Bonferroni)" formula subtext built from the SERVED
    `alpha_per_test`/`n_trials_next` values — never a hardcoded "0.05"), **Thresholdout budget
    remaining** (a new local `formatAlpha` helper — same 4-sig-fig precision as `formatPValue` but
    renders an exact `0` for a fully-spent budget rather than `formatPValue`'s `"< 0.0001"` wording,
    which would be misleading for a legitimate zero), and **Staging LORD++ next-trial level**.
  - Each card carries a **spend-over-time sparkline** (`data-testid="budget-sparkline"`) — a small
    dependency-free inline SVG polyline built from the card's own field in the served
    `spend_over_time` array (trial index for the trials card; `required_p` for the required-p and
    staging cards; `alpha_charged` for the Thresholdout card, so its spend EVENTS are visible even
    though the headline is a running total). The four small series didn't warrant pulling in
    `lightweight-charts` (already a project dependency, used elsewhere for real interactive charts) —
    the plan explicitly allowed either approach and named "simpler" as the tiebreaker.
  - Three explicit states: a **loading skeleton** (`data-testid="budget-skeleton"`, four card-shaped
    placeholders), a **fetch-error card** ("Backend unavailable", nav intact — mirrors `/research/
    graveyard`'s error card verbatim), and the **honest zero/empty snapshot** — NOT a fourth branch:
    when the served payload reports 0 trials (missing/empty ledger), the same four cards render
    naturally with `0` / `0.05` / `1` / the staging initial-wealth value and an empty-series sparkline
    placeholder ("No trials yet") — this is the payload's honest natural output, not a defensive stub.
  - No forms, no mutations, no proven-language anywhere (no "Proven"/"Not yet proven" badge or text).

- **Research hub update** (`apps/frontend/app/research/page.tsx`) — a **third card** in the EXISTING
  "Governance & process" grid (already `xl:grid-cols-3`, previously 2/3 full with registry + graveyard),
  linking to `/research/budget`, `data-testid="research-governance-link-budget"` (the exact testid the
  spec names), a `Wallet` icon (checked against the 13 icons already imported on that page — no
  collision). Same card markup/hover/focus treatment as the two existing cards. The section's header
  comment was updated to reflect "registry + graveyard + budget now; referee-audit still to follow" — a
  documentation-accuracy edit only, no structural/behavioral change to the two existing cards.

- **`lib/budget.ts`** (new) — `BudgetSpendPoint` / `CanonicalBudget` / `StagingBudget` / `BudgetResponse`
  types, mirroring `lib/graveyard.ts`'s types-only pattern (no exported logic — nothing to unit-test,
  same precedent as `lib/graveyard.ts`/`lib/registry.ts` carrying no companion test file).

- **`lib/api.ts`** — `fetchBudget(signal?)` calling `GET /api/research/budget`, following the exact
  shape of the existing `fetchGraveyard`; re-exports the new budget types alongside the existing
  evidence/registry/graveyard type re-exports.

- **J-19 (registry lineage-scroll fix)**: NO code change made or needed. Confirmed
  `apps/frontend/app/research/registry/page.tsx:50-59`'s `useEffect` (the `#registration-<id>`
  hash-scroll-into-view effect that fires after rows mount, fixing the SPA-navigation case where the
  browser's native fragment scroll fires before the client-fetched rows exist) is present and
  untouched. I did not open this file for editing.

## Design System Compliance

- Used the existing `Card`/`CardContent`, `PageHeading` components throughout — no raw HTML where a
  component exists. (`Badge` was not needed — this page has no status/verdict chips, only numeric
  stat cards.)
- Card/typography/spacing tokens match `/research/graveyard` and `/research/registry` exactly:
  `border-border bg-surface` cards, `text-xs uppercase tracking-wide text-text-faint` labels,
  `text-text-muted` secondary text, the shared `num` class for numeric values.
- No new visual effects (no glow/gradient/glassmorphism) — a calm, data-first stat-card grid, matching
  the plan's Visual Requirements ("minimal, matching the existing Research governance pages").
- The sparkline SVG uses only `text-accent` (`currentColor`) — no arbitrary hex/rgba colors.
- Hover/focus states on the new hub card match the existing two cards exactly (same
  `hover:border-accent hover:bg-surface-2` / `focus-visible:ring-1 focus-visible:ring-accent` classes).
- Responsive: the hub's governance grid is unchanged in structure (`sm:grid-cols-2 xl:grid-cols-3`, now
  with a third card filling it); the budget page's own stat grid is `grid-cols-1 sm:grid-cols-2
  xl:grid-cols-4` (a 1x4/2x2-at-smaller-widths layout, per the plan's Visual Requirements).
- No "Proven"/"Not yet proven" `Badge` anywhere (anti-goal #1 — explicitly out of scope for this page).

## Files Changed

- `apps/frontend/lib/budget.ts` -- NEW. Types only.
- `apps/frontend/lib/api.ts` -- added `fetchBudget`, re-exported budget types.
- `apps/frontend/app/research/budget/page.tsx` -- NEW. The four-card accounting panel.
- `apps/frontend/app/research/page.tsx` -- third governance-grid card; header comment updated.

## Tests Run

- `npx tsc --noEmit` -- clean, zero type errors, from `apps/frontend/`. Run twice (once mid-development,
  once as a final check after all edits) — both clean.
- `next lint` -- not configured in this repo (no committed ESLint config; running it triggers an
  interactive first-time-setup prompt) — skipped, matching iter-30/31 precedent.
- No `lib/budget.test.ts` was written — the module carries only type declarations (no exported pure
  logic), matching `lib/graveyard.ts`/`lib/registry.ts`'s own precedent (this codebase's `node
  lib/*.test.ts` harness is also separately non-functional in this sandbox, per the iter-30/31 dev
  handoffs' documented environment gap — unrelated to any file changed here).
- Live smoke test against a running `scripts/dev.sh` instance (backend :8255, frontend :3255, prod
  build cache cleared first via `rm -rf apps/frontend/.next`):
  - `curl http://localhost:3255/research/budget` -> HTTP 200, no error markers, "Certification-budget
    accounting" present in the SSR shell, no "proven"/"Proven" text anywhere.
  - `curl http://localhost:3255/research` -> HTTP 200, HTML contains
    `data-testid="research-governance-link-budget"` and "Certification-budget accounting" (the new hub
    card server-renders into the initial HTML).
  - `curl http://localhost:3255/research/graveyard` and `/research/registry` -> both still HTTP 200, no
    error markers (regression check — neither page's own code was touched this iteration).
  - Frontend dev-server log shows clean compiles for every route touched
    (`✓ Compiled /research/budget in 513ms`), zero errors/warnings.
  - The four cards' populated numbers and sparklines themselves (fetched client-side via `useEffect`,
    per this codebase's established "use client" + fetch-on-mount pattern) do not appear in a plain
    `curl` of the server-rendered shell — expected Next.js behavior for a client component's async
    data, not a bug. Interactive verification (the four cards showing byte-matching numbers against the
    live `GET /api/research/budget` response, and the sparklines rendering) is the browser-qa-agent's
    job downstream.
  - Verified the SAME live payload's raw numbers by hand against the rendered subtext formulas:
    `required_p=0.00625` == `0.05 ÷ 8`; `alpha_budget_remaining=0.9` of `alpha_budget_total=1`, spent
    `0.1` == `0.05 + 0.05` (the two charged trials in the real ledger).

## Known Issues

See `docs/handoffs/goal-mcp-loop-iter-32-dev.md` — Known Issues (no browser click-through performed by
me — by design, reserved for the canonical browser-qa-agent lane; the unfilled project-template.md;
the demo-narrator walkthrough is a downstream step; the pre-existing environment/pipeline-artifact
state note). Nothing frontend-specific beyond what that section already covers.
