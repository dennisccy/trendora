# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-106 — "Proximity to 52w high" column on `/stocks`
- A new column **"Proximity to 52w high"** in the Stock Leaderboard table, **directly after the Risk
  column** and before Setup. It shows each stock's stored distance below its 52-week high (a percent
  ≤ 0; `0.00%` at a fresh high; muted **NA** on short history) — read verbatim from the already-served
  Leadership `high_proximity` component (no recompute, no new fetch, no payload change).
- The column header is a **sortable** control (existing `SortHeader`): clicking it sorts the leaderboard
  by proximity; clicking again toggles direction. **NA always sorts last**, in either direction. The sort
  button's accessible name is `Sort by Proximity to 52w high`.
- The header carries the config-backed glossary **info tooltip** (`TermInfo term="52-week high
  proximity"`) — the SAME single glossary catalog every other tooltip reads (no hard-coded copy).
- The cell matches the other numeric leaderboard cells (right-aligned `num`); NA renders as a muted "NA"
  exactly like the forward-return / max-drawdown cells.
- **Consistency with the Stock Detail page:** the Leadership component breakdown's "Proximity to 52w
  high" row now shows the SAME formatted distance value (e.g. `-0.53%`) as the leaderboard column — they
  read and format the identical served value via one shared helper (`lib/high-proximity.ts`). Previously
  the breakdown showed an opaque percentile for this one component.

### J-108 — honest readiness badge on every page
- The top-bar readiness badge now correctly reads **Ready** / **Initializing… history n/m** /
  **Backend unavailable** based on the real backend state — including when the app is opened at the
  `dev.sh`-printed **LAN-IP** address (previously it was stuck on "Backend unavailable" there). No new UI
  surface — the badge component and its three honest states are unchanged; only the request path it (and
  every page's data fetch) uses was corrected.

## How to Verify (operator, ~3 min)

1. `./scripts/dev.sh`, then open the **LAN-IP** URL it prints (e.g. `http://192.168.1.68:3255`), not just
   localhost. Within a couple of seconds the top-bar badge should read **Initializing… history n/m** and
   then **Ready** — NOT "Backend unavailable".
2. Stop the backend only → the badge should flip to **Backend unavailable** (honest, not faked).
3. Go to `/stocks`. Confirm a **"Proximity to 52w high"** column appears right after **Risk**. Click its
   header → the table reorders by proximity (an indicator arrow appears on that header). Click again →
   order reverses; any NA rows stay at the bottom both times.
4. Open a stock's detail page; in the Leadership "component breakdown", the **Proximity to 52w high** row
   shows the SAME value as that ticker's cell in the leaderboard column.
5. Hover the column header's info icon → the glossary definition of "52-week high proximity" appears.

## Files Changed (frontend)

- `apps/frontend/lib/api-base.ts` (NEW) — host-aware base resolver (pure function).
- `apps/frontend/lib/api-base.test.ts` (NEW) — unit assertions for the resolver.
- `apps/frontend/lib/api.ts` — runtime host-aware `apiBase()` in `getJSON`/`sendJSON` (SSR-guarded).
- `apps/frontend/lib/high-proximity.ts` (NEW) — shared read + format helpers (single source).
- `apps/frontend/components/component-breakdown.tsx` — `high_proximity` row shows the raw distance value.
- `apps/frontend/app/stocks/page.tsx` — new column (header + cell), `high_proximity` sort key, NA-last comparator, `HighProximityCell`, glossary tooltip.

## Design-System Notes

- No new colors, effects, or components — reuses the existing leaderboard `<table>`, `SortHeader`,
  `TermInfo`/`InfoTooltip`, and the muted-NA pattern from `ForwardReturnCell`. Right-aligned `num` cell
  matches the existing numeric columns. Hover/focus/active states are inherited from `SortHeader`.

## Known Limitations

- No live NA row was available to screenshot (all current warm rows have full 52w history), so the muted
  "NA" + NA-last behavior is logic/unit-verified rather than browser-captured this run.
- The host-aware base only changes behavior when the configured base is localhost AND the page host is
  non-localhost; an explicit `NEXT_PUBLIC_API_URL` is always used verbatim.
