# Phase goal-mcp-loop-iter-31 — UI Surface Map

**Phase:** goal-mcp-loop-iter-31 (goal mode, journey J-19 / backlog B-902)
**Date:** 2026-07-13
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, applied to every file listed in the dev/frontend handoffs (verified against the actual diffs, not paraphrased):

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/graveyard.py` (NEW) | backend-internal | indirect | Pure read-compose module (`build_graveyard_payload`, `resolve_staging_ledger_path`, `REVISIT_PROTOCOL`). No direct UI coupling itself — it is the sole data source for the endpoint below. |
| `apps/backend/app/api/graveyard.py` (NEW) | backend-api | indirect — confirmed consumed | New `GET /api/research/graveyard`. Confirmed consumed: `apps/frontend/lib/api.ts` calls it via `fetchGraveyard()`, rendered by `/research/graveyard`. Surface is affected. |
| `apps/backend/main.py` (router wiring, +2 lines) | backend-internal (wiring) | indirect | Registers `graveyard.router`. No UI surface of its own; enables the endpoint above to be reachable. |
| `apps/backend/tests/test_graveyard.py` (NEW) | tests | none | Test coverage only. |
| `apps/backend/tests/test_api_graveyard.py` (NEW) | tests | none | Test coverage only. |
| `apps/backend/tests/test_registry.py` (extended, +1 test) | tests | none | Drift-insurance assertion only; no existing test altered. |
| `apps/frontend/lib/graveyard.ts` (NEW) | frontend-direct (data/types layer) | indirect | `GraveyardEntry`/`RevisitProtocol`/`GraveyardResponse` types. No rendering of its own; consumed by the new page. |
| `apps/frontend/lib/api.ts` (modified) | frontend-direct (data layer) | indirect | Adds `fetchGraveyard()` + re-exports graveyard types — the fetch call the new page uses. |
| `apps/frontend/app/research/graveyard/page.tsx` (NEW) | frontend-direct | direct | New page — the entire graveyard table + revisit-protocol UI. |
| `apps/frontend/app/research/page.tsx` (modified) | frontend-direct | direct | Existing hub page — new card added to the "Governance & process" grid. |
| `apps/frontend/app/research/registry/page.tsx` (modified) | frontend-direct | direct (presentation-only) | Existing page — row `id`/`scroll-mt-20` addition enables deep-linking; no data/visual change under normal browsing. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/graveyard` | `GraveyardPage` — full table (`data-testid="graveyard-table"`) | New page | Ships J-19: browse every referee-rejected hypothesis across both the canonical and staging ledgers | Navigate to `/research/graveyard` directly (or via the `/research` hub card). Confirm the table renders 14 rows (`data-testid="graveyard-row"`, ×14): 7 tagged `canonical` and 7 tagged `staging` in the Ledger column. Confirm the row whose Selectors chips read `strategy=ma_stack` (or equivalent) has Selectors/Verdict/Date matching that entry's raw line in `certified-claims.jsonl` byte-for-byte. |
| `/research/graveyard` | Verdict badge (`data-testid="graveyard-verdict"`) | New component | Show `FAIL`/`INSUFFICIENT` without ever implying "proven" | For every row, confirm the badge text is exactly `FAIL` or `INSUFFICIENT`, rendered in the `danger` (red) or `warn` (amber) Badge color — never the green `accent` "Proven" styling used on `/evidence`. |
| `/research/graveyard` | "permanent" pill (`data-testid="graveyard-permanent"`) | New component | Flags a hypothesis whose matched registration has `status === "closed"` (e.g. `ma_stack`) — must never be silently retried | Locate the closed-hypothesis row and confirm a "permanent" pill is visible beside its Verdict badge; confirm no other (non-closed) row shows this pill. |
| `/research/graveyard` | Deflation cell (`data-testid="graveyard-deflation"`) | New information displayed | Surfaces the referee's multiple-testing correction context verbatim, never recomputed | Read a `canonical`-ledger row's Deflation cell and confirm it reads `bonferroni ÷8`; read a `staging`-ledger row's cell and confirm it shows the raw `deflation`/`deflation_divisor` values from that entry (e.g. `lord++ ÷1`) — must match the ledger file's fields exactly, not a recalculated number. |
| `/research/graveyard` | Ledger origin pill (`data-testid="graveyard-ledger"`) | New information displayed | The staging (internal exploration) ledger's rejected ideas become visible for the first time anywhere in the product | Confirm exactly 7 rows show a `staging` pill and 7 rows show a `canonical` pill (14 total); confirm no other page in the product displays `staging`-origin data. |
| `/research/graveyard` | Lineage link / honest-null text (`data-testid="graveyard-lineage-link"` / `data-testid="graveyard-lineage-none"`) | New feature | Traces a rejected hypothesis back to its pre-registration entry, reusing `registry.match_registration` (no second matcher) | Click a row's Lineage link (renders as `<registration-id> →`) and confirm the browser navigates to `/research/registry#registration-<id>` and the page scrolls to position that exact `<tr>` beneath the header (not the page top). Since every real entry today is matched, the "No registration lineage" text path can only be confirmed via the backend fixture tests (`test_graveyard.py`), not live data — note this as a known live-data gap, not a bug. |
| `/research/graveyard` | "Revisit protocol →" row link + panel (`data-testid="graveyard-row-revisit-link"`, `data-testid="graveyard-revisit-protocol"`, panel `id="revisit-protocol"`) | New component | Explains the rule for when (if ever) a rejected idea may be re-tested | Click any row's "Revisit protocol →" link and confirm the page scrolls to the panel with `id="revisit-protocol"`, showing rule text beginning "A referee FAIL/INSUFFICIENT is final for that hypothesis...". |
| `/research/graveyard` | Loading / error / empty states | New feature | Graceful degrade (anti-goal: never a blank crash on data-shape/availability change) | Reload `/research/graveyard` and confirm a pulsing 8-bar skeleton appears briefly before the table. Stop the backend and reload to confirm a "Backend unavailable" card (red-bordered) appears instead of a crash or blank page. (Fixture-only, not reachable with live data) confirm an all-empty-ledger scenario renders `data-testid="graveyard-empty"` with the text "No rejected hypotheses yet". |
| `/research` | Governance & process grid — new card (`data-testid="research-governance-link-graveyard"`) | Added navigation | Discoverability entry point for the new graveyard page | On `/research`, confirm a card titled "Negative-results graveyard" (Archive icon) appears as the second item in the `data-testid="research-governance"` grid, beside "Pre-registration registry". Click it and confirm navigation lands on `/research/graveyard`. |
| `/research/registry` | Row anchor — `id="registration-<id>"` + `scroll-mt-20` added to `data-testid="registry-row"` | Changed behavior (presentation-only) | Lets a graveyard Lineage link land on its exact backing row instead of the page top | Copy a row id from a graveyard Lineage link (e.g. `registration-REG-003`), then manually visit `/research/registry#registration-REG-003` directly and confirm the browser scrolls to and positions that exact row below the sticky header. Separately, confirm normal top-to-bottom browsing of `/research/registry` (no fragment) looks pixel-identical to before this iteration — no data, column, or row content changed. |

---

## Backend-Only Changes (No UI Impact)

These have no UI surface of their own; each is a supporting dependency of the `/research/graveyard` surface above and is fully realized through it — none is an unwired "not visible yet" capability.

- `apps/backend/app/engine/graveyard.py` (NEW) — `build_graveyard_payload()`, `resolve_staging_ledger_path()`, `REVISIT_PROTOCOL` constant. Pure read-compose logic; no DB session, no rendering. Feeds `GET /api/research/graveyard` exclusively.
- `apps/backend/main.py` — two-line additive router registration (`graveyard` import + `include_router(graveyard.router, ...)`). No UI surface itself; makes the endpoint above reachable.
- `apps/backend/tests/test_graveyard.py`, `apps/backend/tests/test_api_graveyard.py`, `apps/backend/tests/test_registry.py` (extended) — test coverage only (45 tests total per dev handoff). No UI impact.

---

## Summary

- **Frontend surfaces changed:** 3 (`/research/graveyard` new; `/research` hub modified; `/research/registry` modified)
- **New pages/routes:** 1 (`/research/graveyard`)
- **Modified components:** 2 visible (`/research` governance card; `/research/registry` row anchor) + 2 non-visual supporting data-layer files (`lib/graveyard.ts` new, `lib/api.ts` extended — no independent UI surface)
- **Navigation changes:** yes — new card added to `/research`'s existing "Governance & process" grid; no change to the persistent top-level nav
- **Backend-only changes:** 3 (engine composition module, `main.py` router wiring, 3 test files)
