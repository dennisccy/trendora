# goal-market-compass-iter-40 Frontend Handoff

**Phase:** goal-market-compass-iter-40
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

The What-changed card (`/`) now discloses the complete stock-level accounting the backend serves
(J-15), plus the AG-8 gating passenger fix.

- `apps/frontend/lib/api.ts` — new `SessionDeltaStockAccounting` interface and
  `SessionDelta.stock_accounting?: SessionDeltaStockAccounting` (OPTIONAL — absent on every
  `next_session_manifests` row frozen before this ships). `WhyNotFailedCondition.gating` widened
  from required to `gating?: boolean` (it was always absent, not `false`, on the 21 pre-iter-38
  stored dates — the interface was simply mis-declared).
- `apps/frontend/lib/stock-accounting-summary.ts` (new) — two pure, dependency-free helpers
  (`stockResidualDisclosureText`, `stockShownCapDisclosureText`), extracted so the optional-field
  guard is unit-testable under this project's plain-node/`tsx` convention (mirrors
  `why-not-summary.ts` from iter-39).
- `apps/frontend/components/compass-whatchanged-card.tsx` — renders both helpers' output:
  a "showing the top N stock moves" line beside the stock entries (only when the display cap
  actually held something back this session) and a residual disclosure ("N more stock moves held
  back by the display cap") visibly distinct from the existing "Suppressed moves (N)" line.
- `apps/frontend/components/compass-focus-section.tsx` — the why-not block's per-condition
  `gating` suffix is now a genuine 3-state render (`gatingSuffix()`): not-recorded / gating /
  advisory, instead of the previous 2-state truthiness read that silently mislabeled an absent
  `gating` "— advisory".

## UI Evolution

- **New user-facing capability:** the What-changed card's stock-kind accounting is now complete —
  a reader can tell "this stock did not move enough" (suppressed) from "this stock moved enough
  but isn't in the shown list" (residual), where before the latter simply vanished.
- **New information displayed:**
  - "Suppressed moves (N)" on `/` now includes stock-kind crossings (measured today: 43 more, N
    went from 36 to 79 on the live frontier pair).
  - A new residual disclosure line near the stock section, shown only on manifests minted after
    this change (`stock_accounting` present) — an explicit count, including an honest zero when
    nothing was held back.
  - A "showing the top N stock moves" disclosure beside the shown stock entries, only when the
    display cap actually held something back this session (`residual_count > 0`).
  - The why-not block's per-condition line now distinguishes a genuinely-unchecked (pre-iter-38)
    `gating` value ("— not recorded") from a checked-and-advisory one ("— advisory"), where before
    both rendered identically.
- **New user actions:** none — this is a disclosure-completeness fix to an existing read-only
  card, no new interactive control.
- **UI surface changes:** `/` — What-changed card only (existing card, two additive lines). No new
  page, no nav change, no new component — reuses the existing `Card`/`Disclosure`/`Badge`
  primitives verbatim.
- **Navigation changes:** none.
- **Visual/design-token changes:** none — both new lines use existing `text-xs text-text-faint` /
  `text-xs text-text-muted` utility classes already used elsewhere in this card, no new
  color/spacing/effect.

## Visual verification (live, real browser)

Backend + frontend started via `scripts/start-backend.sh` / `scripts/start-frontend.sh` (ports
8255/3255); both stopped and confirmed dead after verification. This session's `trendora-window`
MCP server (Chrome DevTools Protocol) failed to connect, so verification used the system-installed
Playwright/Chromium directly (`python3.14 -c "from playwright.sync_api import sync_playwright..."`)
— a real headless browser executing the page's client-side fetch/render, not curl.

- `/` (frontier as-of, after minting a new manifest version via the standard authorized
  `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` call to exercise the new fields —
  see the dev handoff for the full API-level verification): rendered body text contained, in
  order, `"...Suppressed moves (79)... 4 more stock moves held back by the display cap... Leadership
  rotation..."` and separately `"...leadership bucket D → E... Showing the top 10 stock moves...
  Suppressed moves (79)..."` — both new lines present, visibly distinct from each other and from
  the suppressed-moves line, no per-name list attached to either.
- `/?asof=2025-04-15` (an older manifest, `stock_accounting` genuinely absent): neither "more
  stock move" nor "Showing the top" text appears anywhere in the rendered page; "Suppressed moves
  (37)" rendered using only its pre-existing sector/theme/breadth/market counts; full page
  render, no "not reachable" / "Application error" text anywhere.
- `/?asof=2001-04-17` (a pre-iter-38 manifest, `failed_conditions[].gating` genuinely absent):
  expanding the "Not priority" disclosure showed
  `"leadership_min_score: 79.4 vs 80.0 (distance 0.6) — not recorded"` for a
  `below_selection_floor` row — the new 3-state label, not the old "— advisory" mislabel and not
  a crash.

## Design system compliance

No new colors, spacing, or effects. Both new lines reuse existing Tailwind utility classes already
present in this exact component (`text-xs text-text-faint`, `text-xs text-text-muted`). No new
component introduced; existing `Card`, `CardContent`, `Disclosure`, `Badge` primitives reused
verbatim.

## Known Issues

- Full click-path acceptance for J-15 plus the ten required-still-passing journeys, and the
  deterministic replay re-run of the two repaired goldens (J-04, J-14), are browser-qa-agent's
  scope per this project's established convention — not run by the developer agent. This
  handoff's own live verification (above) is a targeted developer-level sanity check covering
  every numeric TC the spec names, not a substitute for that full pass.
- `apps/frontend/.next-verify/` remains tracked in git (pre-existing, spec-acknowledged, unrelated
  to this iteration) — its verification-build diffs were cleaned before this handoff.
- The `gatingSuffix()` 3-state render lives inline in `compass-focus-section.tsx` (not extracted
  to `lib/`) since the TESTING REQUIREMENTS section only names a `stock_accounting` guard test as
  the required frontend unit test; it is covered instead by the live TC-9 browser check above.
