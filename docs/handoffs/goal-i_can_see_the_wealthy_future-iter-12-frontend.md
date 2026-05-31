# goal-i_can_see_the_wealthy_future-iter-12 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

- **NEW page `/methodology`** (`apps/frontend/app/methodology/page.tsx`): the Methodology / Glossary. Fetches `GET /api/methodology` and renders each entry as a `Card` — the entry name + a Setup/Pattern `Badge` chip, the plain-language `meaning`, a compact thresholds list (`label cmp value unit`, or a prose `text` rule verbatim), and the worked `example`. Reuses the dense-dark idiom (`PageHeading`, `Card`, palette tokens, monospace `num`) and the established loading-skeleton / "Backend unavailable" error / empty-state patterns. NO hard-coded per-entry copy — every entry comes from the fetched catalog.
- **NEW `components/ui/info-tooltip.tsx`**: a dependency-free, accessible info affordance. Its definition panel is revealed on **hover AND keyboard-focus AND tap/click** (a click pins it open until an outside click or Escape), styled with palette tokens on a Card-like surface. The panel content mounts in the DOM when open, so it is deterministically assertable by browser-QA.
- **NEW sidebar item** (`components/sidebar.tsx`): `{ href: "/methodology", label: "Methodology", icon: BookOpen }` placed after Watchlist — the iteration's nav-skeleton change.
- **`/stocks` badge tooltips** (`app/stocks/page.tsx`): the setup badge now shows the catalog `meaning` for its status via the info tooltip; the VCP badge keeps its per-row reason (native `title`) and additionally exposes the catalog VCP `meaning` via the info tooltip — the same definitions the Methodology page shows.
- **`/stocks` Setup filter is now catalog-driven**: the hard-coded `SETUP_STATUSES` array was removed; the Setup filter options now come from the catalog's `kind:"setup"` entries in catalog order. **Graceful degradation:** if the catalog fetch fails, the filter falls back to the setup statuses present in the data, so the leaderboard and all filters keep working (protects J-02 and warm load J-15).
- **`lib/api.ts`**: added `fetchMethodology(signal?)` plus the `MethodologyCatalog` / `MethodologyEntry` / `MethodologyThresholdRow` types. Throws on non-200 like the other fetchers (explicit "Backend unavailable", never fabricated copy).

## Files Changed

- `apps/frontend/app/methodology/page.tsx` — NEW glossary page.
- `apps/frontend/components/ui/info-tooltip.tsx` — NEW accessible hover/focus/tap tooltip.
- `apps/frontend/components/sidebar.tsx` — added BookOpen import + "Methodology" nav item after Watchlist.
- `apps/frontend/app/stocks/page.tsx` — removed `SETUP_STATUSES`; catalog-sourced Setup filter; wired info-tooltips to the setup + VCP badges; non-blocking catalog fetch with graceful fallback.
- `apps/frontend/lib/api.ts` — `fetchMethodology` + `MethodologyCatalog`/`MethodologyEntry`/`MethodologyThresholdRow` types.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **BUILD_EXIT=0** — Compiled successfully, types valid. App routes **11 → 12**; the new `○ /methodology` route is listed (3.04 kB). No new dependency added.

## Design-System Conformance

- Components: `Card`, `Badge` (existing variants — `accent` for Pattern, `default` for Setup), `PageHeading`, `EmptyState`, monospace `num` for threshold values. The info tooltip uses `--surface` + `--border` on a Card-like surface.
- Palette tokens only (`--accent`, `--surface`/`--surface-2`, `--border`, `--text`/`--text-muted`/`--text-faint`); no arbitrary hex. Spacing on the 4px scale.
- States handled: loading skeleton, "Backend unavailable" error card, empty state on `/methodology`; the tooltip shows on hover/focus/tap and is dismissible (outside-click / Escape); the `/stocks` filter degrades gracefully on a catalog fetch failure.
- Discipline preserved: the UI re-formats server values only — it recomputes no score/bucket/return. `setupVariant` (status→colour) stays in the frontend (pure presentation, not per-entry copy).

## Known Issues

- The info tooltip is an absolutely-positioned pop-over inside the Stocks table (which has `overflow-x-auto`); on the very last visible row the panel can extend just past the table's scroll area. The same definition is always fully visible on the dedicated `/methodology` page, and the panel text is present in the DOM as soon as it is opened (assertable by browser-QA). Acceptable per spec (the setup-badge inline explanation is reachable via click/tap, not title-only).
- Because `NEXT_PUBLIC_API_URL` is inlined at build time, a production `next start` must be built with the correct backend URL; `scripts/start-frontend.sh` (next dev) exports it at runtime for QA.
