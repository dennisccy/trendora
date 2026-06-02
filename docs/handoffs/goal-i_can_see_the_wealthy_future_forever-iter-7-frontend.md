# goal-i_can_see_the_wealthy_future_forever-iter-7 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-7
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete (additive, read-only — J-22 introduces no new user actions)

## What Was Built (UI)

- **`/methodology` — new "Universe Selection" card.** Rendered above the setup/pattern glossary when
  the API returns `universe_selection`. It shows:
  - the **membership-rule prose** (how the universe is sourced + screened),
  - the **resolved universe size** (read from the one canonical universe), and
  - the **three screen thresholds** — minimum market cap, minimum average daily dollar volume, minimum
    share price — each read **live from config** and shown compactly (`$2B` / `$50M` / `$10`).
  - Mirrors the existing config-backed `EntryCard` pattern; uses palette tokens + monospace numbers
    only; no hard-coded copy or numbers (everything comes from the API value). `data-testid`s:
    `universe-selection`, `universe-size`.
- **`/data` (Data Manager) — new "Universe" coverage metric.** The coverage panel now shows the
  **screened universe size** (`coverage.universe_count`) distinct from "Symbols (incl. ETFs)"
  (`symbol_count`, which counts every distinct priced symbol including the benchmark ETFs + ^VIX). The
  grid widened from 5 to 6 metrics. `data-testid`: `universe-count`. The same resolved-universe value
  appears here and on `/methodology` (single source — no drift).

## Files Changed

- `apps/frontend/lib/api.ts` — added the `UniverseSelection` type, `universe_selection?` on
  `MethodologyCatalog`, and `universe_count` on `DataCoverage`.
- `apps/frontend/app/methodology/page.tsx` — `UniverseSelectionCard` + compact `fmtMoney` display
  formatter (display-only; the number is never recomputed client-side).
- `apps/frontend/app/data/page.tsx` — added the "Universe" metric to `CoveragePanel`.

## Discipline / States

- The frontend **re-formats** API values only — it never recomputes membership, the universe size, or a
  threshold. Compact currency (`$2B`) is display formatting of the API number.
- Loading / error / empty states already exist on both pages and are preserved: if the methodology
  payload lacks `universe_selection`, the section is simply not rendered (no fabricated fallback number);
  a backend-unavailable state shows the existing styled error (no fabricated copy).
- Honest-limitation labels elsewhere (breadth "universe-relative", walk-forward "survivorship-biased")
  are untouched.

## Verification Note

`npm run build` (compile + typecheck) should be run as part of QA. The components are additive and use
existing shadcn/ui primitives (`Card`, `Badge`) + palette tokens; no new component-library pieces.
The visible universe size will read its true expanded value once the seed expansion (see the dev
handoff runbook) has been completed.

## Fix Notes (fix cycle 2 — no frontend code change)

**No `.tsx`/`.ts` files changed this cycle.** The honest-gate fix is entirely backend (the API now omits
`universe_selection` until a real screen record exists). The frontend already handles this exactly right —
`app/methodology/page.tsx` renders the "Universe Selection" card **only when** `universe_selection` is
present (see *Discipline / States* above), so today (universe still 122, no screen has run) the card is
**intentionally hidden**. This is the honest state: the product does **not** show a "Screen" card claiming
the current 122 names are a screen result when they are not. The card will appear automatically — with the
real screened members and grown size — the moment the offline screen runs and commits its record. The
`/data` "Universe" metric continues to show the true current universe size (122).

## Fix Notes (fix cycle 3 — no frontend code change)

**No `.tsx`/`.ts` files changed this cycle.** The review's only frontend-adjacent finding is a NOTE
(*"Universe Selection card is implemented correctly but renders nothing because the backing screen record is
absent (gated by design) … No frontend change needed; resolves with the data finish runbook"*). Confirmed: the
card is correct and intentionally hidden until a real screen record exists. The blocker is the unreachable
data provider (fresh probe this cycle: HTTP 429 on both Yahoo hosts + crumb) — not a UI defect. The card and
the `/data` "Universe" figure surface the grown numbers automatically once the offline screen runs.
